"use client";

import React from "react";

interface Suggestion {
    text: string;
    emoji?: string;
}

interface ConversationSuggestionsProps {
    suggestions: Suggestion[];
    onSelect: (text: string) => void;
    className?: string;
}

export default function ConversationSuggestions({
    suggestions,
    onSelect,
    className = "",
}: ConversationSuggestionsProps) {
    if (suggestions.length === 0) return null;

    return (
        <div className={`conversation-suggestions ${className}`}>
            <div className="flex flex-wrap gap-2 justify-center">
                {suggestions.map((suggestion, index) => (
                    <button
                        key={index}
                        onClick={() => onSelect(suggestion.text)}
                        className="suggestion-chip group"
                    >
                        {suggestion.emoji && (
                            <span className="mr-1.5 text-base">{suggestion.emoji}</span>
                        )}
                        <span className="text-sm">{suggestion.text}</span>
                    </button>
                ))}
            </div>
        </div>
    );
}
