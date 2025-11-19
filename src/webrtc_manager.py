import asyncio
import json
import logging
from typing import Dict, Optional, Callable
from datetime import datetime
from aiortc import RTCPeerConnection, RTCSessionDescription, RTCIceCandidate, MediaStreamTrack
from aiortc.contrib.media import MediaPlayer, MediaRecorder

logger = logging.getLogger(__name__)

class VoiceCall:
    """Represents an active or pending voice call"""
    def __init__(self, call_id: str, caller_id: str, callee_id: str, direction: str):
        self.call_id = call_id
        self.caller_id = caller_id
        self.callee_id = callee_id
        self.direction = direction  # 'outgoing' or 'incoming'
        self.status = 'initiating'  # 'initiating', 'ringing', 'connecting', 'active', 'ended'
        self.peer_connection: Optional[RTCPeerConnection] = None
        self.created_at = datetime.now().isoformat()
        self.started_at: Optional[str] = None
        self.ended_at: Optional[str] = None

class WebRTCManager:
    """Manages WebRTC voice calls and peer connections"""
    
    def __init__(self, user_id: str, send_signal_callback: Callable):
        self.user_id = user_id
        self.send_signal = send_signal_callback  # Callback to send signaling messages
        self.active_calls: Dict[str, VoiceCall] = {}
        self.call_handlers = {
            'incoming_call': [],
            'call_accepted': [],
            'call_rejected': [],
            'call_ended': [],
            'call_error': []
        }
        
    def add_call_handler(self, event: str, handler: Callable):
        """Add a handler for call events"""
        if event in self.call_handlers:
            self.call_handlers[event].append(handler)
    
    def _notify_handlers(self, event: str, *args, **kwargs):
        """Notify all handlers for an event"""
        for handler in self.call_handlers.get(event, []):
            try:
                handler(*args, **kwargs)
            except Exception as e:
                logger.error(f"Error in call handler for {event}: {e}")
    
    async def start_call(self, peer_id: str, call_id: str) -> bool:
        """Initiate a voice call to a peer"""
        try:
            # Create voice call object
            call = VoiceCall(call_id, self.user_id, peer_id, 'outgoing')
            self.active_calls[call_id] = call
            
            # Create peer connection
            pc = RTCPeerConnection()
            call.peer_connection = pc
            
            # Setup event handlers
            @pc.on("icecandidate")
            async def on_ice_candidate(candidate):
                if candidate:
                    await self._send_ice_candidate(call_id, peer_id, candidate)
            
            @pc.on("iceconnectionstatechange")
            async def on_ice_connection_state_change():
                logger.info(f"ICE connection state: {pc.iceConnectionState}")
                if pc.iceConnectionState == "connected":
                    call.status = "active"
                    call.started_at = datetime.now().isoformat()
                    self._notify_handlers('call_accepted', call_id, peer_id)
                elif pc.iceConnectionState in ["failed", "closed"]:
                    await self.end_call(call_id)
            
            # Add audio track (microphone)
            try:
                # Create a simple audio track
                # In production, you'd capture from actual microphone
                # For now, we'll add a basic track
                from aiortc.contrib.media import MediaBlackhole
                
                # Create offer
                offer = await pc.createOffer()
                await pc.setLocalDescription(offer)
                
                # Send offer to peer
                await self._send_offer(call_id, peer_id, pc.localDescription)
                
                call.status = 'ringing'
                return True
                
            except Exception as e:
                logger.error(f"Error adding audio track: {e}")
                await self.end_call(call_id)
                return False
                
        except Exception as e:
            logger.error(f"Error starting call: {e}")
            self._notify_handlers('call_error', call_id, str(e))
            return False
    
    async def accept_call(self, call_id: str) -> bool:
        """Accept an incoming voice call"""
        try:
            call = self.active_calls.get(call_id)
            if not call or call.status != 'ringing':
                return False
            
            call.status = 'connecting'
            
            # Peer connection should already be created when offer was received
            pc = call.peer_connection
            if not pc:
                return False
            
            # Create answer
            answer = await pc.createAnswer()
            await pc.setLocalDescription(answer)
            
            # Send answer to peer
            await self._send_answer(call_id, call.caller_id, pc.localDescription)
            
            return True
            
        except Exception as e:
            logger.error(f"Error accepting call: {e}")
            self._notify_handlers('call_error', call_id, str(e))
            return False
    
    async def reject_call(self, call_id: str) -> bool:
        """Reject an incoming voice call"""
        try:
            call = self.active_calls.get(call_id)
            if not call:
                return False
            
            # Send rejection signal
            await self._send_rejection(call_id, call.caller_id)
            
            # Cleanup
            if call.peer_connection:
                await call.peer_connection.close()
            
            call.status = 'ended'
            call.ended_at = datetime.now().isoformat()
            
            self._notify_handlers('call_rejected', call_id, call.caller_id)
            
            return True
            
        except Exception as e:
            logger.error(f"Error rejecting call: {e}")
            return False
    
    async def end_call(self, call_id: str) -> bool:
        """End an active voice call"""
        try:
            call = self.active_calls.get(call_id)
            if not call:
                return False
            
            # Send end signal to peer
            peer_id = call.callee_id if call.direction == 'outgoing' else call.caller_id
            await self._send_end_signal(call_id, peer_id)
            
            # Close peer connection
            if call.peer_connection:
                await call.peer_connection.close()
            
            call.status = 'ended'
            call.ended_at = datetime.now().isoformat()
            
            self._notify_handlers('call_ended', call_id, peer_id)
            
            # Remove from active calls after a delay
            asyncio.create_task(self._cleanup_call(call_id))
            
            return True
            
        except Exception as e:
            logger.error(f"Error ending call: {e}")
            return False
    
    async def _cleanup_call(self, call_id: str, delay: int = 5):
        """Cleanup call after delay"""
        await asyncio.sleep(delay)
        if call_id in self.active_calls:
            del self.active_calls[call_id]
    
    async def handle_signal(self, signal_data: dict) -> bool:
        """Handle incoming WebRTC signaling message"""
        try:
            signal_type = signal_data.get('type')
            call_id = signal_data.get('call_id')
            from_peer = signal_data.get('from_peer')
            
            if signal_type == 'offer':
                return await self._handle_offer(call_id, from_peer, signal_data['sdp'])
            elif signal_type == 'answer':
                return await self._handle_answer(call_id, signal_data['sdp'])
            elif signal_type == 'ice_candidate':
                return await self._handle_ice_candidate(call_id, signal_data['candidate'])
            elif signal_type == 'rejection':
                return await self._handle_rejection(call_id)
            elif signal_type == 'end':
                return await self._handle_end(call_id)
            else:
                logger.warning(f"Unknown signal type: {signal_type}")
                return False
                
        except Exception as e:
            logger.error(f"Error handling signal: {e}")
            return False
    
    async def _handle_offer(self, call_id: str, from_peer: str, sdp: dict) -> bool:
        """Handle incoming call offer"""
        try:
            # Create incoming call
            call = VoiceCall(call_id, from_peer, self.user_id, 'incoming')
            call.status = 'ringing'
            self.active_calls[call_id] = call
            
            # Create peer connection
            pc = RTCPeerConnection()
            call.peer_connection = pc
            
            # Setup event handlers
            @pc.on("icecandidate")
            async def on_ice_candidate(candidate):
                if candidate:
                    await self._send_ice_candidate(call_id, from_peer, candidate)
            
            @pc.on("track")
            def on_track(track):
                logger.info(f"Received track: {track.kind}")
                # In production, play the audio track
            
            @pc.on("iceconnectionstatechange")
            async def on_ice_connection_state_change():
                logger.info(f"ICE connection state: {pc.iceConnectionState}")
                if pc.iceConnectionState == "connected":
                    call.status = "active"
                    call.started_at = datetime.now().isoformat()
                elif pc.iceConnectionState in ["failed", "closed"]:
                    await self.end_call(call_id)
            
            # Set remote description (offer)
            offer = RTCSessionDescription(sdp=sdp['sdp'], type=sdp['type'])
            await pc.setRemoteDescription(offer)
            
            # Notify handlers of incoming call
            self._notify_handlers('incoming_call', call_id, from_peer)
            
            return True
            
        except Exception as e:
            logger.error(f"Error handling offer: {e}")
            return False
    
    async def _handle_answer(self, call_id: str, sdp: dict) -> bool:
        """Handle call answer"""
        try:
            call = self.active_calls.get(call_id)
            if not call or not call.peer_connection:
                return False
            
            # Set remote description (answer)
            answer = RTCSessionDescription(sdp=sdp['sdp'], type=sdp['type'])
            await call.peer_connection.setRemoteDescription(answer)
            
            call.status = 'connecting'
            
            return True
            
        except Exception as e:
            logger.error(f"Error handling answer: {e}")
            return False
    
    async def _handle_ice_candidate(self, call_id: str, candidate_data: dict) -> bool:
        """Handle ICE candidate"""
        try:
            call = self.active_calls.get(call_id)
            if not call or not call.peer_connection:
                return False
            
            candidate = RTCIceCandidate(
                sdpMid=candidate_data['sdpMid'],
                sdpMLineIndex=candidate_data['sdpMLineIndex'],
                candidate=candidate_data['candidate']
            )
            
            await call.peer_connection.addIceCandidate(candidate)
            
            return True
            
        except Exception as e:
            logger.error(f"Error handling ICE candidate: {e}")
            return False
    
    async def _handle_rejection(self, call_id: str) -> bool:
        """Handle call rejection"""
        call = self.active_calls.get(call_id)
        if call:
            if call.peer_connection:
                await call.peer_connection.close()
            call.status = 'ended'
            self._notify_handlers('call_rejected', call_id, call.callee_id)
            await self._cleanup_call(call_id, delay=1)
        return True
    
    async def _handle_end(self, call_id: str) -> bool:
        """Handle call end"""
        call = self.active_calls.get(call_id)
        if call:
            if call.peer_connection:
                await call.peer_connection.close()
            call.status = 'ended'
            call.ended_at = datetime.now().isoformat()
            peer_id = call.callee_id if call.direction == 'outgoing' else call.caller_id
            self._notify_handlers('call_ended', call_id, peer_id)
            await self._cleanup_call(call_id, delay=1)
        return True
    
    # Signaling message senders
    async def _send_offer(self, call_id: str, peer_id: str, description):
        """Send offer to peer"""
        signal = {
            'type': 'offer',
            'call_id': call_id,
            'from_peer': self.user_id,
            'sdp': {
                'type': description.type,
                'sdp': description.sdp
            }
        }
        await self.send_signal(peer_id, signal)
    
    async def _send_answer(self, call_id: str, peer_id: str, description):
        """Send answer to peer"""
        signal = {
            'type': 'answer',
            'call_id': call_id,
            'from_peer': self.user_id,
            'sdp': {
                'type': description.type,
                'sdp': description.sdp
            }
        }
        await self.send_signal(peer_id, signal)
    
    async def _send_ice_candidate(self, call_id: str, peer_id: str, candidate):
        """Send ICE candidate to peer"""
        signal = {
            'type': 'ice_candidate',
            'call_id': call_id,
            'from_peer': self.user_id,
            'candidate': {
                'sdpMid': candidate.sdpMid,
                'sdpMLineIndex': candidate.sdpMLineIndex,
                'candidate': candidate.candidate
            }
        }
        await self.send_signal(peer_id, signal)
    
    async def _send_rejection(self, call_id: str, peer_id: str):
        """Send rejection to peer"""
        signal = {
            'type': 'rejection',
            'call_id': call_id,
            'from_peer': self.user_id
        }
        await self.send_signal(peer_id, signal)
    
    async def _send_end_signal(self, call_id: str, peer_id: str):
        """Send end signal to peer"""
        signal = {
            'type': 'end',
            'call_id': call_id,
            'from_peer': self.user_id
        }
        await self.send_signal(peer_id, signal)
    
    def get_active_call(self, call_id: str) -> Optional[VoiceCall]:
        """Get an active call by ID"""
        return self.active_calls.get(call_id)
    
    def get_all_active_calls(self) -> list:
        """Get all active calls"""
        return list(self.active_calls.values())
