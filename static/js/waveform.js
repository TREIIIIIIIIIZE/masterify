/**
 * Waveform Visualization
 * 
 * Provides waveform visualization for audio files in the Masterify application
 */

class WaveformVisualizer {
    /**
     * Create a new waveform visualizer
     * @param {HTMLCanvasElement} canvas - The canvas element to draw on
     * @param {Object} options - Configuration options
     */
    constructor(canvas, options = {}) {
        this.canvas = canvas;
        this.ctx = canvas.getContext('2d');
        
        // Default options
        this.options = {
            waveColor: '#6366F1', // Primary color (indigo)
            progressColor: '#10B981', // Accent color (emerald)
            backgroundColor: 'transparent',
            barWidth: 2,
            barGap: 1,
            barRadius: 0,
            responsive: true,
            cursorWidth: 2,
            cursorColor: 'rgba(0, 0, 0, 0.5)',
            ...options
        };
        
        // Initialize properties
        this.data = [];
        this.duration = 0;
        this.currentTime = 0;
        this.isPlaying = false;
        this.animationId = null;
        
        // Set up resize handler if responsive
        if (this.options.responsive) {
            this._resizeHandler = this._onResize.bind(this);
            window.addEventListener('resize', this._resizeHandler);
            this._setCanvasSize();
        } else {
            this._setCanvasSize(this.options.width, this.options.height);
        }
    }
    
    /**
     * Load waveform data
     * @param {Array} data - Array of normalized amplitude values (0-1)
     * @param {number} duration - Audio duration in seconds
     */
    loadData(data, duration = 0) {
        this.data = data;
        this.duration = duration;
        this.draw();
        return this;
    }
    
    /**
     * Set the current playback position
     * @param {number} time - Current time in seconds
     */
    setCurrentTime(time) {
        this.currentTime = Math.max(0, Math.min(time, this.duration));
        if (!this.isPlaying) {
            this.draw();
        }
        return this;
    }
    
    /**
     * Start playback visualization
     */
    play() {
        if (this.isPlaying) return this;
        
        this.isPlaying = true;
        const startTime = performance.now() - (this.currentTime * 1000);
        
        const animate = (now) => {
            if (!this.isPlaying) return;
            
            this.currentTime = (now - startTime) / 1000;
            if (this.currentTime >= this.duration) {
                this.currentTime = this.duration;
                this.isPlaying = false;
            }
            
            this.draw();
            
            if (this.isPlaying) {
                this.animationId = requestAnimationFrame(animate);
            }
        };
        
        this.animationId = requestAnimationFrame(animate);
        return this;
    }
    
    /**
     * Pause playback visualization
     */
    pause() {
        this.isPlaying = false;
        if (this.animationId) {
            cancelAnimationFrame(this.animationId);
            this.animationId = null;
        }
        return this;
    }
    
    /**
     * Draw the waveform
     */
    draw() {
        const { ctx, canvas, options, data } = this;
        const { width, height } = canvas;
        
        // Clear canvas
        ctx.fillStyle = options.backgroundColor;
        ctx.fillRect(0, 0, width, height);
        
        if (!data || data.length === 0) return this;
        
        const totalBars = Math.floor(width / (options.barWidth + options.barGap));
        const barCount = Math.min(totalBars, data.length);
        const barAndGapWidth = options.barWidth + options.barGap;
        
        // Calculate progress position
        const progress = this.duration > 0 ? this.currentTime / this.duration : 0;
        const progressX = Math.floor(width * progress);
        
        // Draw bars
        for (let i = 0; i < barCount; i++) {
            const x = i * barAndGapWidth;
            const dataIndex = Math.floor((i / barCount) * data.length);
            const value = data[dataIndex] || 0;
            
            // Calculate bar height (0.05 minimum for visibility)
            const barHeight = Math.max(value * height * 0.9, height * 0.05);
            const y = (height - barHeight) / 2;
            
            // Determine color based on progress
            ctx.fillStyle = x < progressX ? options.progressColor : options.waveColor;
            
            // Draw rounded bars if radius is set
            if (options.barRadius > 0) {
                this._drawRoundedBar(x, y, options.barWidth, barHeight, options.barRadius);
            } else {
                ctx.fillRect(x, y, options.barWidth, barHeight);
            }
        }
        
        // Draw playback cursor
        if (options.cursorWidth > 0 && this.duration > 0) {
            ctx.fillStyle = options.cursorColor;
            ctx.fillRect(progressX - options.cursorWidth / 2, 0, options.cursorWidth, height);
        }
        
        return this;
    }
    
    /**
     * Draw a rounded bar
     * @private
     */
    _drawRoundedBar(x, y, width, height, radius) {
        const { ctx } = this;
        
        // Ensure radius doesn't exceed half of width or height
        radius = Math.min(radius, width / 2, height / 2);
        
        ctx.beginPath();
        ctx.moveTo(x + radius, y);
        ctx.lineTo(x + width - radius, y);
        ctx.quadraticCurveTo(x + width, y, x + width, y + radius);
        ctx.lineTo(x + width, y + height - radius);
        ctx.quadraticCurveTo(x + width, y + height, x + width - radius, y + height);
        ctx.lineTo(x + radius, y + height);
        ctx.quadraticCurveTo(x, y + height, x, y + height - radius);
        ctx.lineTo(x, y + radius);
        ctx.quadraticCurveTo(x, y, x + radius, y);
        ctx.closePath();
        ctx.fill();
    }
    
    /**
     * Handle window resize events
     * @private
     */
    _onResize() {
        this._setCanvasSize();
        this.draw();
    }
    
    /**
     * Set canvas size based on container
     * @private
     */
    _setCanvasSize(width, height) {
        if (width && height) {
            this.canvas.width = width;
            this.canvas.height = height;
        } else if (this.options.responsive) {
            // Get the size from the parent element
            const container = this.canvas.parentNode;
            if (container) {
                this.canvas.width = container.clientWidth;
                this.canvas.height = container.clientHeight;
            }
        }
    }
    
    /**
     * Clean up resources
     */
    destroy() {
        this.pause();
        if (this._resizeHandler) {
            window.removeEventListener('resize', this._resizeHandler);
        }
    }
}

// Export as global variable for use in other scripts
window.WaveformVisualizer = WaveformVisualizer;
