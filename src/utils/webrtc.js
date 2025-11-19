/**
 * WebRTC Client Utility for WhisperLink Voice Calls
 * Handles client-side WebRTC operations
 */

class WebRTCClient {
    constructor(executeCommand) {
        this.executeCommand = executeCommand;
        this.activeCalls = new Map();
        this.localStream = null;
    }

    /**
     * Initialize microphone access
     */
    async initializeMicrophone() {
        try {
            if (this.localStream) {
                return this.localStream;
            }

            this.localStream = await navigator.mediaDevices.getUserMedia({
                audio: {
                    echoCancellation: true,
                    noiseSuppression: true,
                    autoGainControl: true
                },
                video: false
            });

            return this.localStream;
        } catch (error) {
            console.error('Failed to access microphone:', error);
            throw new Error('Microphone access denied. Please allow microphone access to make voice calls.');
        }
    }

    /**
     * Start a voice call
     */
    async startCall(peerId) {
        try {
            // Initialize microphone
            await this.initializeMicrophone();

            // Request backend to start call
            const result = await this.executeCommand('start_voice_call', { peer_id: peerId });

            if (result.success) {
                return {
                    success: true,
                    callId: result.call_id
                };
            } else {
                throw new Error(result.error || 'Failed to start call');
            }
        } catch (error) {
            console.error('Error starting call:', error);
            return {
                success: false,
                error: error.message
            };
        }
    }

    /**
     * Accept an incoming call
     */
    async acceptCall(callId) {
        try {
            // Initialize microphone
            await this.initializeMicrophone();

            // Request backend to accept call
            const result = await this.executeCommand('accept_voice_call', { call_id: callId });

            if (result.success) {
                return { success: true };
            } else {
                throw new Error(result.error || 'Failed to accept call');
            }
        } catch (error) {
            console.error('Error accepting call:', error);
            return {
                success: false,
                error: error.message
            };
        }
    }

    /**
     * Reject an incoming call
     */
    async rejectCall(callId) {
        try {
            const result = await this.executeCommand('reject_voice_call', { call_id: callId });

            if (result.success) {
                return { success: true };
            } else {
                throw new Error(result.error || 'Failed to reject call');
            }
        } catch (error) {
            console.error('Error rejecting call:', error);
            return {
                success: false,
                error: error.message
            };
        }
    }

    /**
     * End an active call
     */
    async endCall(callId) {
        try {
            const result = await this.executeCommand('end_voice_call', { call_id: callId });

            // Stop local stream
            if (this.localStream) {
                this.localStream.getTracks().forEach(track => track.stop());
                this.localStream = null;
            }

            if (result.success) {
                return { success: true };
            } else {
                throw new Error(result.error || 'Failed to end call');
            }
        } catch (error) {
            console.error('Error ending call:', error);
            return {
                success: false,
                error: error.message
            };
        }
    }

    /**
     * Get pending incoming calls
     */
    async getPendingCalls() {
        try {
            const result = await this.executeCommand('get_pending_calls', {});

            if (result.success) {
                return {
                    success: true,
                    calls: result.calls || []
                };
            } else {
                return {
                    success: false,
                    calls: []
                };
            }
        } catch (error) {
            console.error('Error getting pending calls:', error);
            return {
                success: false,
                calls: []
            };
        }
    }

    /**
     * Get active calls
     */
    async getActiveCalls() {
        try {
            const result = await this.executeCommand('get_active_calls');

            if (result.success) {
                return {
                    success: true,
                    calls: result.calls || []
                };
            } else {
                return {
                    success: false,
                    calls: []
                };
            }
        } catch (error) {
            console.error('Error getting active calls:', error);
            return {
                success: false,
                calls: []
            };
        }
    }

    /**
     * Mute/unmute microphone
     */
    setMuted(muted) {
        if (this.localStream) {
            this.localStream.getAudioTracks().forEach(track => {
                track.enabled = !muted;
            });
            return true;
        }
        return false;
    }

    /**
     * Check if microphone is available
     */
    async checkMicrophoneAvailable() {
        try {
            const devices = await navigator.mediaDevices.enumerateDevices();
            return devices.some(device => device.kind === 'audioinput');
        } catch (error) {
            console.error('Error checking microphone:', error);
            return false;
        }
    }

    /**
     * Cleanup
     */
    cleanup() {
        if (this.localStream) {
            this.localStream.getTracks().forEach(track => track.stop());
            this.localStream = null;
        }
        this.activeCalls.clear();
    }
}

export default WebRTCClient;
