"use client";

import React from "react";

interface VoiceControlsProps {
    isPlaying: boolean;
    onPauseResume: () => void;
    volume: number;
    onVolumeChange: (volume: number) => void;
    showVolumeControl?: boolean;
}

export default function VoiceControls({
    isPlaying,
    onPauseResume,
    volume,
    onVolumeChange,
    showVolumeControl = true,
}: VoiceControlsProps) {
    return (
        <div className="voice-controls flex items-center gap-3">
            {/* Pause/Resume Button */}
            <button
                onClick={onPauseResume}
                className="voice-control-btn"
                title={isPlaying ? "Pause" : "Resume"}
            >
                {isPlaying ? (
                    <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 24 24">
                        <path d="M6 4h4v16H6V4zm8 0h4v16h-4V4z" />
                    </svg>
                ) : (
                    <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 24 24">
                        <path d="M8 5v14l11-7z" />
                    </svg>
                )}
            </button>

            {/* Speaking Indicator */}
            {isPlaying && (
                <div className="flex items-center gap-1">
                    <div className="waveform-bar"></div>
                    <div className="waveform-bar" style={{ animationDelay: "0.1s" }}></div>
                    <div className="waveform-bar" style={{ animationDelay: "0.2s" }}></div>
                    <div className="waveform-bar" style={{ animationDelay: "0.3s" }}></div>
                </div>
            )}

            {/* Volume Control */}
            {showVolumeControl && (
                <div className="flex items-center gap-2">
                    <svg className="w-4 h-4 text-gray-500" fill="currentColor" viewBox="0 0 24 24">
                        <path d="M3 9v6h4l5 5V4L7 9H3zm13.5 3c0-1.77-1.02-3.29-2.5-4.03v8.05c1.48-.73 2.5-2.25 2.5-4.02z" />
                    </svg>
                    <input
                        type="range"
                        min="0"
                        max="100"
                        value={volume}
                        onChange={(e) => onVolumeChange(Number(e.target.value))}
                        className="volume-slider"
                    />
                </div>
            )}
        </div>
    );
}
