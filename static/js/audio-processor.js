/**
 * Audio Processor
 * 
 * Client-side audio processing and analysis for the Masterify application.
 * Works in coordination with the server-side processing by providing 
 * visualizations and real-time feedback.
 */

class AudioProcessor {
    constructor() {
        this.audioContext = null;
        this.audioBuffer = null;
        this.sourceNode = null;
        this.analyserNode = null;
        this.isPlaying = false;
        this.visualizationData = [];
    }
    
    /**
     * Initialize the Web Audio API context
     */
    initAudioContext() {
        try {
            // Create new AudioContext (or use the existing one)
            if (!this.audioContext) {
                window.AudioContext = window.AudioContext || window.webkitAudioContext;
                this.audioContext = new AudioContext();
            }
            
            // Create analyzer for visualizations
            this.analyserNode = this.audioContext.createAnalyser();
            this.analyserNode.fftSize = 2048;
            this.bufferLength = this.analyserNode.frequencyBinCount;
            
            return true;
        } catch (e) {
            console.error('Web Audio API is not supported in this browser', e);
            return false;
        }
    }
    
    /**
     * Load an audio file from a URL or File object
     * @param {string|File} source - URL or File object
     * @returns {Promise} - Resolves when audio is loaded
     */
    loadAudio(source) {
        return new Promise((resolve, reject) => {
            if (!this.audioContext) {
                if (!this.initAudioContext()) {
                    reject(new Error('Failed to initialize audio context'));
                    return;
                }
            }
            
            // If audioContext is suspended (autoplay policy), resume it
            if (this.audioContext.state === 'suspended') {
                this.audioContext.resume();
            }
            
            // Handle different source types
            if (typeof source === 'string') {
                // URL string
                fetch(source)
                    .then(response => response.arrayBuffer())
                    .then(arrayBuffer => this.decodeAudio(arrayBuffer))
                    .then(audioBuffer => {
                        this.audioBuffer = audioBuffer;
                        this.generateVisualizationData();
                        resolve(audioBuffer);
                    })
                    .catch(error => {
                        console.error('Error loading audio from URL:', error);
                        reject(error);
                    });
            } else if (source instanceof File) {
                // File object
                const reader = new FileReader();
                
                reader.onload = (e) => {
                    this.decodeAudio(e.target.result)
                        .then(audioBuffer => {
                            this.audioBuffer = audioBuffer;
                            this.generateVisualizationData();
                            resolve(audioBuffer);
                        })
                        .catch(error => {
                            console.error('Error decoding audio file:', error);
                            reject(error);
                        });
                };
                
                reader.onerror = (e) => {
                    console.error('Error reading file:', e);
                    reject(new Error('Error reading file'));
                };
                
                reader.readAsArrayBuffer(source);
            } else {
                reject(new Error('Invalid source type. Expected URL string or File object.'));
            }
        });
    }
    
    /**
     * Decode audio data from ArrayBuffer
     * @param {ArrayBuffer} arrayBuffer - Audio data
     * @returns {Promise} - Resolves with decoded AudioBuffer
     */
    decodeAudio(arrayBuffer) {
        return this.audioContext.decodeAudioData(arrayBuffer);
    }
    
    /**
     * Play loaded audio
     * @returns {boolean} - Success status
     */
    playAudio() {
        if (!this.audioBuffer || !this.audioContext) {
            console.error('No audio loaded');
            return false;
        }
        
        // Stop currently playing audio if any
        if (this.isPlaying) {
            this.stopAudio();
        }
        
        // Create source node
        this.sourceNode = this.audioContext.createBufferSource();
        this.sourceNode.buffer = this.audioBuffer;
        
        // Connect nodes: source -> analyser -> destination
        this.sourceNode.connect(this.analyserNode);
        this.analyserNode.connect(this.audioContext.destination);
        
        // Start playback
        this.sourceNode.start(0);
        this.isPlaying = true;
        
        // Set up ended event
        this.sourceNode.onended = () => {
            this.isPlaying = false;
            this.sourceNode.disconnect();
            this.sourceNode = null;
        };
        
        return true;
    }
    
    /**
     * Stop audio playback
     */
    stopAudio() {
        if (this.sourceNode && this.isPlaying) {
            this.sourceNode.stop();
            this.sourceNode.disconnect();
            this.sourceNode = null;
            this.isPlaying = false;
        }
    }
    
    /**
     * Generate visualization data from the audio buffer
     * @param {number} dataPoints - Number of data points to generate (default: 100)
     * @returns {Array} - Array of normalized amplitude values
     */
    generateVisualizationData(dataPoints = 100) {
        if (!this.audioBuffer) {
            console.error('No audio loaded');
            return [];
        }
        
        const channelData = this.audioBuffer.getChannelData(0); // Use first channel
        const blockSize = Math.floor(channelData.length / dataPoints);
        const visualizationData = [];
        
        for (let i = 0; i < dataPoints; i++) {
            const blockStart = blockSize * i;
            let sum = 0;
            
            // Find the maximum value in this block
            for (let j = 0; j < blockSize; j++) {
                const value = Math.abs(channelData[blockStart + j]);
                sum = Math.max(sum, value);
            }
            
            // Add normalized value to visualization data
            visualizationData.push(sum);
        }
        
        // Normalize values between 0 and 1
        const max = Math.max(...visualizationData);
        if (max > 0) {
            for (let i = 0; i < visualizationData.length; i++) {
                visualizationData[i] /= max;
            }
        }
        
        this.visualizationData = visualizationData;
        return visualizationData;
    }
    
    /**
     * Get real-time frequency data for visualizations
     * @returns {Uint8Array} - Frequency data
     */
    getFrequencyData() {
        if (!this.analyserNode) return null;
        
        const dataArray = new Uint8Array(this.analyserNode.frequencyBinCount);
        this.analyserNode.getByteFrequencyData(dataArray);
        return dataArray;
    }
    
    /**
     * Get real-time time domain data for visualizations
     * @returns {Uint8Array} - Time domain data
     */
    getTimeDomainData() {
        if (!this.analyserNode) return null;
        
        const dataArray = new Uint8Array(this.analyserNode.frequencyBinCount);
        this.analyserNode.getByteTimeDomainData(dataArray);
        return dataArray;
    }
    
    /**
     * Analyze audio to suggest appropriate presets
     * Simple client-side analysis for UI feedback
     * @returns {Object} - Analysis results
     */
    analyzeAudio() {
        if (!this.audioBuffer) {
            console.error('No audio loaded');
            return null;
        }
        
        const channelData = this.audioBuffer.getChannelData(0);
        const length = channelData.length;
        
        // Calculate RMS (volume)
        let sumSquares = 0;
        for (let i = 0; i < length; i++) {
            sumSquares += channelData[i] * channelData[i];
        }
        const rms = Math.sqrt(sumSquares / length);
        
        // Calculate peak amplitude
        let peak = 0;
        for (let i = 0; i < length; i++) {
            peak = Math.max(peak, Math.abs(channelData[i]));
        }
        
        // Calculate crest factor (dynamic range)
        const crestFactor = peak / rms;
        
        // Calculate zero-crossing rate (rough frequency approximation)
        let zeroCrossings = 0;
        for (let i = 1; i < length; i++) {
            if ((channelData[i] >= 0 && channelData[i-1] < 0) || 
                (channelData[i] < 0 && channelData[i-1] >= 0)) {
                zeroCrossings++;
            }
        }
        const zeroCrossingRate = zeroCrossings / length;
        
        // Simple preset suggestion
        let suggestedPreset = 'clean'; // Default
        
        if (crestFactor < 4) {
            // Compressed audio, likely lofi or trap
            if (zeroCrossingRate < 0.1) {
                // Low frequencies dominant
                suggestedPreset = 'trap';
            } else {
                suggestedPreset = 'lofi';
            }
        } else if (crestFactor > 10) {
            // Wide dynamic range, likely acoustic
            suggestedPreset = 'warm';
        } else if (zeroCrossingRate > 0.15) {
            // High frequencies dominant
            suggestedPreset = 'bright';
        }
        
        return {
            duration: this.audioBuffer.duration,
            channels: this.audioBuffer.numberOfChannels,
            sampleRate: this.audioBuffer.sampleRate,
            rms: rms,
            peak: peak,
            crestFactor: crestFactor,
            zeroCrossingRate: zeroCrossingRate,
            suggestedPreset: suggestedPreset
        };
    }
    
    /**
     * Clean up resources
     */
    dispose() {
        this.stopAudio();
        
        if (this.analyserNode) {
            this.analyserNode.disconnect();
            this.analyserNode = null;
        }
        
        if (this.audioContext) {
            this.audioContext.close().catch(e => console.error('Error closing AudioContext:', e));
            this.audioContext = null;
        }
        
        this.audioBuffer = null;
        this.visualizationData = [];
    }
}

// Export as global variable for use in other scripts
window.AudioProcessor = AudioProcessor;
