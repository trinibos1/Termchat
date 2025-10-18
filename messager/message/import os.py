import os
import asyncio
from typing import Tuple, Optional, List, Dict, Any

import requests

# Ensure LOGGER, and any other globals are defined/imported in your project
# from your_project.logging import LOGGER

class BackendAsync:
    # Assumes __init__ sets self.client, self._user, etc.
    def __init__(self, client, user, logger):
        self.client = client
        self._user = user
        self._logger = logger
        global LOGGER
        LOGGER = logger

    # Placeholder helpers - your real implementations should exist.
    def _auth_headers(self) -> Dict[str, str]:
        # Your existing implementation should return headers dict.
        if self._user and getattr(self._user, "access_token", None):
            return {"Authorization": f"Bearer {self._user.access_token}"}
        return {}

    async def _run_maybe_async(self, fn_or_query, *args, **kwargs):
        # Your real implementation likely checks if fn_or_query is callable (sync/async)
        # or an object (query) and runs it accordingly. This preserves behavior but
        # does NOT pass headers into sync execute() functions.
        # If fn_or_query is a callable, call it. If it's an object (query), return it directly
        # so that supabase-py shows it to the user (client displays query if needed).
        if callable(fn_or_query):
            result = fn_or_query(*args, **kwargs)
            if asyncio.iscoroutine(result):
                return await result
            return result
        else:
            # If a non-callable (likely a query object that the client can await), try awaiting it
            try:
                maybe_coro = fn_or_query
                if asyncio.iscoroutine(maybe_coro):
                    return await maybe_coro
                return maybe_coro
            except Exception as e:
                # Fallback: return object
                return fn_or_query

    def _normalize_resp(self, resp) -> Tuple[Any, Optional[str]]:
        """
        Normalize supabase-py responses. Adjust depending on supabase-py version.
        Common shapes:
         - resp is a tuple (data, count) or (data, error)
         - resp is a requests-like Response with .json() and .status_code
         - resp is dict/list directly
        This simple normalizer tries common patterns and returns (data, error_message).
        """
        try:
            # If it's a requests Response
            if hasattr(resp, "status_code") and hasattr(resp, "json"):
                try:
                    body = resp.json()
                except Exception:
                    body = {"text": resp.text}
                if 200 <= resp.status_code < 300:
                    return body, None
                # error shape
                if isinstance(body, dict):
                    msg = body.get("error") or body.get("message") or body.get("details")
                    if not msg and isinstance(body.get("error"), dict):
                        msg = body["error"].get("message")
                    return None, msg or f"HTTP {resp.status_code}"
                return None, f"HTTP {resp.status_code}"
            # If it's a tuple (data, error) or (data, count)
            if isinstance(resp, (list, tuple)) and len(resp) >= 1:
                # supabase-py sometimes returns (data, count) or (data, error)
                data = resp[0]
                # try to infer error from second value
                err = None
                if len(resp) > 1:
                    second = resp[1]
                    if isinstance(second, dict) and second.get("message"):
                        err = second.get("message")
                return data, err
            # If dict/list directly
            if isinstance(resp, (dict, list)):
                return resp, None
            # Unknown shape — return as data
            return resp, None
        except Exception as e:
            LOGGER.exception("_normalize_resp failed")
            return None, "Failed to parse response"

    # -------------------------
    # Contacts
    # -------------------------
    async def add_contact(self, owner_id: str, contact_email: str, use_edge: bool = False) -> Tuple[bool, Optional[str]]:
        """
        Add a contact. By default performs direct PostgREST insert via supabase-py.
        If use_edge=True, calls the add_contact_server Edge Function which handles
        lookup, duplicate checks, and insertion server-side.
        """
        if use_edge:
            return await self.add_contact_via_edge(contact_email)

        try:
            headers = self._auth_headers()
            query = self.client.table("profiles").select("id,email,username").eq("email", contact_email).maybe_single()
            exec_fn = getattr(query, "execute", None)
            if exec_fn:
                resp = await self._run_maybe_async(exec_fn)
            else:
                resp = await self._run_maybe_async(query)
            data, err = self._normalize_resp(resp)
            if err:
                LOGGER.debug("add_contact: lookup error %s", err)
                return False, "Contact with this email not found."
            if not data:
                return False, "Contact with this email not found."
            contact_id = data.get("id")
            if contact_id == owner_id:
                return False, "Cannot add yourself as contact."

            # check for existing contact to return friendly error
            check_q = self.client.table("contacts").select("id").eq("owner_id", owner_id).eq("contact_id", contact_id)
            exec_fn2 = getattr(check_q, "execute", None)
            if exec_fn2:
                check_resp = await self._run_maybe_async(exec_fn2)
            else:
                check_resp = await self._run_maybe_async(check_q)
            existing, exist_err = self._normalize_resp(check_resp)
            if exist_err:
                LOGGER.debug("add_contact: existing check error %s", exist_err)
            if existing and isinstance(existing, list) and len(existing) > 0:
                return False, "Contact already exists."

            insert_q = self.client.table("contacts").insert({"owner_id": owner_id, "contact_id": contact_id})
            exec_fn3 = getattr(insert_q, "execute", None)
            if exec_fn3:
                resp2 = await self._run_maybe_async(exec_fn3)
            else:
                resp2 = await self._run_maybe_async(insert_q)
            _, err2 = self._normalize_resp(resp2)
            if err2:
                return False, err2
            return True, None
        except Exception:
            LOGGER.exception("add_contact failed")
            return False, "Failed to add contact"

    async def add_contact_via_edge(self, contact_email: str) -> Tuple[bool, Optional[str]]:
        """
        Call the add_contact_server Edge Function that was deployed.
        Expects the current user to be authenticated (self._user.access_token present).
        """
        if not self._user or not getattr(self._user, "access_token", None):
            return False, "Not authenticated"

        supabase_url = os.getenv("SUPABASE_URL")
        if not supabase_url:
            return False, "SUPABASE_URL not set in environment"

        edge_url = supabase_url.rstrip("/") + "/functions/v2/add_contact_server"
        headers = {
            "Authorization": f"Bearer {self._user.access_token}",
            "Content-Type": "application/json",
        }
        try:
            loop = asyncio.get_event_loop()

            def _post():
                return requests.post(edge_url, headers=headers, json={"email": contact_email}, timeout=10)

            resp = await loop.run_in_executor(None, _post)
            try:
                body = resp.json()
            except Exception:
                body = {"text": resp.text}

            if resp.status_code in (200, 201):
                return True, None
            # normalize common PostgREST/edge error shapes
            msg = None
            if isinstance(body, dict):
                msg = body.get("error") or body.get("message") or body.get("details")
                if not msg and isinstance(body.get("error"), dict):
                    msg = body["error"].get("message")
            if not msg:
                msg = f"Edge function error: HTTP {resp.status_code}"
            LOGGER.debug("add_contact_via_edge response: %s", body)
            return False, msg
        except Exception:
            LOGGER.exception("add_contact_via_edge failed")
            return False, "Failed to call edge function"

    # -------------------------
    # Messaging
    # -------------------------
    async def send_message(self, sender_id: str, receiver_email: str, content: str) -> Tuple[bool, Optional[str]]:
        if not content or not content.strip():
            return False, "Message content empty"
        try:
            headers = self._auth_headers()
            # Find receiver id
            query = self.client.table("profiles").select("id,email").eq("email", receiver_email).maybe_single()
            exec_fn = getattr(query, "execute", None)
            if exec_fn:
                resp = await self._run_maybe_async(exec_fn)
            else:
                resp = await self._run_maybe_async(query)
            data, err = self._normalize_resp(resp)
            if err or not data:
                return False, "Recipient not found"
            receiver_id = data.get("id")
            insert_q = self.client.table("messages").insert({"sender_id": sender_id, "receiver_id": receiver_id, "content": content})
            exec_fn2 = getattr(insert_q, "execute", None)
            if exec_fn2:
                resp2 = await self._run_maybe_async(exec_fn2)
            else:
                resp2 = await self._run_maybe_async(insert_q)
            _, err2 = self._normalize_resp(resp2)
            if err2:
                return False, err2
            return True, None
        except Exception:
            LOGGER.exception("send_message failed")
            return False, "Failed to send message"

    async def get_messages(self, user_id: str) -> List[Dict[str, Any]]:
        try:
            headers = self._auth_headers()
            q = self.client.table("messages").select("*").or_(f"sender_id.eq.{user_id},receiver_id.eq.{user_id}").order("created_at", desc=True)
            exec_fn = getattr(q, "execute", None)
            if exec_fn:
                resp = await self._run_maybe_async(exec_fn)
            else:
                resp = await self._run_maybe_async(q)
            data, err = self._normalize_resp(resp)
            if err:
                LOGGER.debug("get_messages: query error: %s", err)
                return []
            return data or []
        except Exception:
            LOGGER.exception("get_messages failed")
            return [