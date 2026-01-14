"use client";

import React, { useEffect, useRef, useState, useCallback } from "react";
import ConversationSuggestions from "./ConversationSuggestions";
import VoiceControls from "./VoiceControls";

type ArchitectureMode = "chained" | "realtime";

interface VoiceChatInterfaceProps {
  sessionId: string;
  grade: string;
  userName: string;
  intent: string;
}

interface Message {
  id: string;
  role: "user" | "assistant";
  text: string;
  audioUrl?: string;
  timestamp: Date;
}

const BACKEND = process.env.NEXT_PUBLIC_BACKEND_ORIGIN || "http://localhost:8000";

export default function VoiceChatInterface({
  sessionId,
  grade,
  userName,
  intent,
}: VoiceChatInterfaceProps) {
  const [messages, setMessages] = useState<Message[]>([]);
  const [isRecording, setIsRecording] = useState(false);
  const [isProcessing, setIsProcessing] = useState(false);
  const [wsStatus, setWsStatus] = useState<"connecting" | "connected" | "disconnected">("disconnected");
  const [inputText, setInputText] = useState("");
  const [currentTranscript, setCurrentTranscript] = useState("");
  const [architectureMode, setArchitectureMode] = useState<ArchitectureMode>("chained");
  const [showSuggestions, setShowSuggestions] = useState(true);
  const [currentLanguage, setCurrentLanguage] = useState<'english' | 'hindi'>('english');
  const [isAudioPlaying, setIsAudioPlaying] = useState(false);
  const [playingAudioId, setPlayingAudioId] = useState<string | null>(null);
  const [audioVolume, setAudioVolume] = useState(100);

  const wsRef = useRef<WebSocket | null>(null);
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const audioChunksRef = useRef<Blob[]>([]);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const audioRef = useRef<HTMLAudioElement | null>(null);
  const audioContextRef = useRef<AudioContext | null>(null);
  const realtimeAudioBufferRef = useRef<Float32Array[]>([]);
  const speechRecognitionRef = useRef<any>(null);

  // Scroll to bottom when new messages arrive
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  // Fetch architecture mode from backend config
  useEffect(() => {
    const fetchConfig = async () => {
      try {
        const res = await fetch(`${BACKEND}/config`);
        const config = await res.json();
        if (config.architecture === "realtime" || config.architecture === "chained") {
          setArchitectureMode(config.architecture);
        }
      } catch (e) {
        console.warn("Failed to fetch config, using default chained mode");
      }
    };
    fetchConfig();
  }, []);

  // Connect WebSocket after architecture mode is determined
  useEffect(() => {
    connectWebSocket();
    return () => {
      wsRef.current?.close();
      audioContextRef.current?.close();
    };
  }, [sessionId, architectureMode]);

  const connectWebSocket = useCallback(() => {
    // Choose endpoint based on architecture mode
    const wsEndpoint = architectureMode === "realtime" ? "/ws/realtime" : "/ws";
    const wsUrl = BACKEND.replace(/^https?:/, (m) => (m === "https:" ? "wss:" : "ws:")) + `${wsEndpoint}?session_id=${sessionId}`;
    setWsStatus("connecting");

    const ws = new WebSocket(wsUrl);
    wsRef.current = ws;

    ws.onopen = () => {
      setWsStatus("connected");
      // Initialize audio context for realtime mode
      if (architectureMode === "realtime") {
        audioContextRef.current = new AudioContext({ sampleRate: 24000 });
      }
    };
    ws.onclose = () => { setWsStatus("disconnected"); };
    ws.onerror = () => { setWsStatus("disconnected"); };

    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);

        // Handle different message types
        if (data.type === "final") {
          // Chained mode: complete response with audio URL
          const audioUrl = data.audio_url ? `${BACKEND}${data.audio_url}` : undefined;
          addMessage("assistant", data.text, audioUrl);
          setIsProcessing(false);
          // Audio is NOT auto-played - user clicks "Play Audio" button

          // Detect language from AI response (Devanagari script = Hindi)
          const hasDevanagari = /[\u0900-\u097F]/.test(data.text);
          if (hasDevanagari) {
            setCurrentLanguage('hindi');
          } else {
            setCurrentLanguage('english');
          }
        }
        else if (data.type === "transcription") {
          // Chained mode: user's speech transcription
          setCurrentTranscript(data.text);
          addMessage("user", data.text);
        }
        else if (data.type === "transcript") {
          // Realtime mode: assistant's speech transcription
          addMessage("assistant", data.text);
          setIsProcessing(false);
        }
        else if (data.type === "audio") {
          // Realtime mode: audio chunk (base64 PCM16)
          playRealtimeAudio(data.audio);
        }
        else if (data.type === "connected") {
          // Realtime mode: connected confirmation
          console.log("Realtime session established");
        }
        else if (data.type === "error") {
          console.error("WebSocket error:", data.message);
          addMessage("assistant", `Error: ${data.message}`);
        }
      } catch (e) { console.error("WS message parse error:", e); }
    };
  }, [sessionId, architectureMode]);

  const addMessage = (role: "user" | "assistant", text: string, audioUrl?: string) => {
    const msg: Message = { id: Date.now().toString(), role, text, audioUrl, timestamp: new Date() };
    setMessages((prev) => [...prev, msg]);
  };

  const playAudio = async (url: string, messageId: string) => {
    try {
      // If same audio is playing, pause it
      if (playingAudioId === messageId && isAudioPlaying && audioRef.current) {
        audioRef.current.pause();
        setIsAudioPlaying(false);
        setPlayingAudioId(null);
        return;
      }

      // Stop any currently playing audio
      if (audioRef.current) {
        audioRef.current.pause();
        audioRef.current = null;
      }

      const audio = new Audio(url);
      audio.volume = audioVolume / 100;
      audioRef.current = audio;

      setIsAudioPlaying(true);
      setPlayingAudioId(messageId);

      audio.onended = () => {
        setIsAudioPlaying(false);
        setPlayingAudioId(null);
      };

      audio.onerror = () => {
        setIsAudioPlaying(false);
        setPlayingAudioId(null);
      };

      await audio.play();
    } catch (e) {
      console.warn("Audio playback error:", e);
      setIsAudioPlaying(false);
      setPlayingAudioId(null);
    }
  };

  const pauseResumeAudio = () => {
    if (audioRef.current) {
      if (isAudioPlaying) {
        audioRef.current.pause();
        setIsAudioPlaying(false);
      } else {
        audioRef.current.play();
        setIsAudioPlaying(true);
      }
    }
  };

  const handleVolumeChange = (volume: number) => {
    setAudioVolume(volume);
    if (audioRef.current) {
      audioRef.current.volume = volume / 100;
    }
  };

  const playRealtimeAudio = async (audioB64: string) => {
    // Realtime mode: decode and play PCM16 audio
    if (!audioContextRef.current) return;

    try {
      const audioData = atob(audioB64);
      const pcm16 = new Int16Array(audioData.length / 2);
      for (let i = 0; i < pcm16.length; i++) {
        pcm16[i] = audioData.charCodeAt(i * 2) | (audioData.charCodeAt(i * 2 + 1) << 8);
      }

      // Convert to float32 for Web Audio API
      const float32 = new Float32Array(pcm16.length);
      for (let i = 0; i < pcm16.length; i++) {
        float32[i] = pcm16[i] / 32768;
      }

      // Create audio buffer and play
      const buffer = audioContextRef.current.createBuffer(1, float32.length, 24000);
      buffer.copyToChannel(float32, 0);

      const source = audioContextRef.current.createBufferSource();
      source.buffer = buffer;
      source.connect(audioContextRef.current.destination);
      source.start();
    } catch (e) {
      console.warn("Realtime audio playback error:", e);
    }
  };

  const sendMessage = (text: string) => {
    if (!text.trim() || wsStatus !== "connected") return;

    // Detect language change requests
    const lowerText = text.toLowerCase();
    if (lowerText.includes("hindi") || lowerText.includes("हिंदी")) {
      setCurrentLanguage('hindi');
    } else if (lowerText.includes("english") || lowerText.includes("अंग्रेजी")) {
      setCurrentLanguage('english');
    }

    addMessage("user", text);
    wsRef.current?.send(JSON.stringify({ type: "text", text }));
    setIsProcessing(true);
    setInputText("");
    setShowSuggestions(false);
  };

  const handleSuggestionClick = (text: string) => {
    sendMessage(text);
  };

  const startRecording = async () => {
    try {
      // Use Web Speech API for browser-based transcription (free, no backend needed)
      const SpeechRecognition = (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;

      if (!SpeechRecognition) {
        // Fallback: show error and suggest typing
        alert("Speech recognition not supported in this browser. Please use Chrome, Edge, or Safari, or type your message.");
        return;
      }

      const recognition = new SpeechRecognition();
      speechRecognitionRef.current = recognition;

      recognition.continuous = true;
      recognition.interimResults = true;
      recognition.lang = currentLanguage === 'hindi' ? 'hi-IN' : 'en-US';

      let finalTranscript = '';

      recognition.onresult = (event: any) => {
        let interimTranscript = '';
        for (let i = event.resultIndex; i < event.results.length; i++) {
          const transcript = event.results[i][0].transcript;
          if (event.results[i].isFinal) {
            finalTranscript += transcript + ' ';
          } else {
            interimTranscript += transcript;
          }
        }
        setCurrentTranscript(finalTranscript + interimTranscript);
      };

      recognition.onerror = (event: any) => {
        console.error('Speech recognition error:', event.error);
        if (event.error === 'not-allowed') {
          alert('Microphone access denied. Please allow microphone access in your browser settings.');
        }
        setIsRecording(false);
      };

      recognition.onend = () => {
        // Recognition ended - set recording to false
        // Note: Don't send message here, stopRecording handles it
        setIsRecording(false);
      };

      recognition.start();
      setIsRecording(true);
      setCurrentTranscript("");
    } catch (e) {
      console.error("Speech recognition error:", e);
      alert("Could not start speech recognition. Please check microphone permissions.");
    }
  };

  const startRealtimeRecording = async (stream: MediaStream) => {
    // For realtime mode, use AudioWorklet to stream PCM16 audio
    if (!audioContextRef.current) {
      audioContextRef.current = new AudioContext({ sampleRate: 24000 });
    }

    const source = audioContextRef.current.createMediaStreamSource(stream);
    const processor = audioContextRef.current.createScriptProcessor(4096, 1, 1);

    processor.onaudioprocess = (e) => {
      if (!isRecording || wsStatus !== "connected") return;

      const inputData = e.inputBuffer.getChannelData(0);
      // Convert float32 to PCM16
      const pcm16 = new Int16Array(inputData.length);
      for (let i = 0; i < inputData.length; i++) {
        pcm16[i] = Math.max(-32768, Math.min(32767, inputData[i] * 32768));
      }

      // Convert to base64 and send
      const bytes = new Uint8Array(pcm16.buffer);
      const b64 = btoa(String.fromCharCode(...bytes));
      wsRef.current?.send(JSON.stringify({ type: "audio", audio: b64 }));
    };

    source.connect(processor);
    processor.connect(audioContextRef.current.destination);

    // Store for cleanup
    (mediaRecorderRef.current as any) = { stream, source, processor };
  };

  const stopRecording = () => {
    if (speechRecognitionRef.current) {
      // Web Speech API mode: stop recognition and send message
      const transcript = currentTranscript.trim();
      speechRecognitionRef.current.stop();
      speechRecognitionRef.current = null; // Clear ref to prevent double handling
      if (transcript) {
        sendMessage(transcript);
      }
    } else if (architectureMode === "realtime") {
      // Realtime mode: commit audio and cleanup
      wsRef.current?.send(JSON.stringify({ type: "audio_commit" }));
      const refs = mediaRecorderRef.current as any;
      if (refs?.stream) {
        refs.stream.getTracks().forEach((t: MediaStreamTrack) => t.stop());
        refs.source?.disconnect();
        refs.processor?.disconnect();
      }
    } else {
      // Chained mode: stop MediaRecorder
      if (mediaRecorderRef.current?.state !== "inactive") {
        mediaRecorderRef.current?.stop();
      }
    }
    setIsRecording(false);
    setCurrentTranscript("");
  };

  const uploadAndTranscribe = async () => {
    setIsProcessing(true);
    const blob = new Blob(audioChunksRef.current, { type: "audio/webm" });
    const formData = new FormData();
    formData.append("file", blob, `recording-${Date.now()}.webm`);
    formData.append("user_id", sessionId);

    try {
      const res = await fetch(`${BACKEND}/upload_audio`, { method: "POST", body: formData });
      const data = await res.json();
      if (data.ok) {
        const filename = data.filename;
        // Poll for transcription
        for (let i = 0; i < 30; i++) {
          await new Promise((r) => setTimeout(r, 1000));
          const tRes = await fetch(`${BACKEND}/transcription/${encodeURIComponent(filename)}`);
          const tData = await tRes.json();
          if (tData.ok && tData.transcription && !tData.transcription.startsWith("(")) {
            const transcript = tData.transcription.trim();
            setCurrentTranscript(transcript);
            sendMessage(transcript);
            return;
          }
        }
        setIsProcessing(false);
      }
    } catch (e) { console.error("Upload error:", e); setIsProcessing(false); }
  };

  const downloadTranscript = () => {
    window.open(`${BACKEND}/sessions/${sessionId}/transcript`, "_blank");
  };

  const getInitialSuggestions = () => {
    const suggestions = [
      { text: "Tell me about admission process", emoji: "📝" },
      { text: "What are the fees?", emoji: "💰" },
      { text: "Can I get a demo class?", emoji: "🎥" },
      { text: "What subjects are covered?", emoji: "📚" },
    ];

    if (intent === "Admission") {
      return [
        { text: "What documents are needed?", emoji: "📄" },
        { text: "When can I enroll?", emoji: "📅" },
        { text: "How long does admission take?", emoji: "⏱️" },
        { text: "Is there an entrance test?", emoji: "✍️" },
      ];
    } else if (intent === "Fees") {
      return [
        { text: "What is the total fee?", emoji: "💰" },
        { text: "Are there payment plans?", emoji: "💳" },
        { text: "Any discounts available?", emoji: "🎁" },
        { text: "What does the fee include?", emoji: "📦" },
      ];
    }

    return suggestions;
  };

  const getContextualSuggestions = () => {
    // Dynamic language toggle based on current conversation language
    const languageOption = currentLanguage === 'hindi'
      ? { text: "Explain in English", emoji: "🇬🇧" }
      : { text: "Explain in Hindi", emoji: "🇮🇳" };

    return [
      { text: "Tell me more", emoji: "💬" },
      languageOption,
      { text: "What about fees?", emoji: "💰" },
      { text: "How do I enroll?", emoji: "📝" },
    ];
  };

  return (
    <div className="h-screen flex flex-col bg-gradient-to-b from-gray-50 to-gray-100">
      {/* Fixed Header - Responsive */}
      <header className="bg-white border-b border-gray-200 px-3 sm:px-4 py-2 sm:py-3 flex items-center justify-between shadow-sm flex-shrink-0">
        <div className="flex items-center gap-2 sm:gap-3">
          <a href="/" className="p-1.5 sm:p-2 hover:bg-gray-100 rounded-full transition-colors">
            <svg className="w-4 h-4 sm:w-5 sm:h-5 text-gray-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
            </svg>
          </a>
          <div className="flex items-center gap-2 sm:gap-3">
            <div className="w-8 h-8 sm:w-10 sm:h-10 rounded-full bg-gradient-to-br from-green-500 to-emerald-600 flex items-center justify-center text-white font-bold text-sm sm:text-base">
              V
            </div>
            <div>
              <h1 className="font-semibold text-gray-900 text-sm sm:text-base">Vikalp AI Voice Tutor</h1>
              <p className="text-[10px] sm:text-xs text-gray-500 truncate max-w-[120px] sm:max-w-none">{grade} • {userName}</p>
            </div>
          </div>
        </div>
        <div className="flex items-center gap-1 sm:gap-2">
          {/* Connection Status */}
          <div className="flex items-center gap-1 px-1.5 sm:px-2 py-1 bg-gray-100 rounded-full">
            <span className={`w-1.5 h-1.5 sm:w-2 sm:h-2 rounded-full ${wsStatus === "connected" ? "bg-green-500" : wsStatus === "connecting" ? "bg-yellow-500 animate-pulse" : "bg-red-500"}`} />
            <span className="text-[10px] sm:text-xs text-gray-600 hidden xs:inline">{wsStatus === "connected" ? "Online" : wsStatus === "connecting" ? "..." : "Offline"}</span>
          </div>
          {isAudioPlaying && (
            <span className="flex items-center gap-1 px-1.5 sm:px-2 py-1 bg-green-100 text-green-700 rounded-full text-[10px] sm:text-xs">
              <span className="animate-pulse">🔊</span>
              <span className="hidden sm:inline">Playing</span>
            </span>
          )}
          <button onClick={downloadTranscript} className="p-1.5 sm:p-2 hover:bg-gray-100 rounded-full transition-colors" title="Download Transcript">
            <svg className="w-4 h-4 sm:w-5 sm:h-5 text-gray-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
            </svg>
          </button>
        </div>
      </header>

      {/* Messages Area */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {messages.length === 0 && (
          <div className="text-center py-8">
            <div className="text-5xl mb-4">🎙️</div>
            <h2 className="text-xl font-semibold text-gray-900 mb-2">Hello, {userName}!</h2>
            <p className="text-gray-600 max-w-md mx-auto mb-4">
              I&apos;m your Vikalp AI Voice Tutor for {grade}. Ask me about {intent.toLowerCase()},
              or anything else about our school. Speak or type your question!
            </p>
            {showSuggestions && (
              <ConversationSuggestions
                suggestions={getInitialSuggestions()}
                onSelect={handleSuggestionClick}
                className="mt-4"
              />
            )}
          </div>
        )}

        {messages.map((msg) => (
          <div key={msg.id} className={`flex ${msg.role === "user" ? "justify-end" : "justify-start"} mb-3`}>
            {msg.role === "assistant" && (
              <div className="w-8 h-8 rounded-full bg-gradient-to-br from-green-500 to-emerald-600 flex items-center justify-center text-white text-sm font-bold mr-2 flex-shrink-0">
                V
              </div>
            )}
            <div className={`max-w-[75%] ${msg.role === "user"
              ? "bg-gradient-to-br from-green-500 to-green-600 text-white rounded-2xl rounded-tr-sm"
              : "bg-white border border-gray-200 shadow-sm rounded-2xl rounded-tl-sm"
              } px-4 py-3`}>
              <p className={`text-sm leading-relaxed whitespace-pre-wrap ${msg.role === "assistant" ? "text-gray-800" : ""}`}>
                {msg.text}
              </p>
              {msg.audioUrl && msg.role === "assistant" && (
                <button
                  onClick={() => playAudio(msg.audioUrl!, msg.id)}
                  className={`mt-3 flex items-center gap-2 px-3 py-1.5 rounded-full text-xs font-medium transition-colors border ${playingAudioId === msg.id && isAudioPlaying
                    ? "bg-red-50 hover:bg-red-100 text-red-700 border-red-200"
                    : "bg-green-50 hover:bg-green-100 text-green-700 border-green-200"
                    }`}
                >
                  {playingAudioId === msg.id && isAudioPlaying ? (
                    <>
                      <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 24 24">
                        <path d="M6 19h4V5H6v14zm8-14v14h4V5h-4z" />
                      </svg>
                      Pause
                    </>
                  ) : (
                    <>
                      <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 24 24">
                        <path d="M8 5v14l11-7z" />
                      </svg>
                      Play Audio
                    </>
                  )}
                </button>
              )}
            </div>
          </div>
        ))}

        {!showSuggestions && messages.length > 0 && messages[messages.length - 1].role === "assistant" && (
          <ConversationSuggestions
            suggestions={getContextualSuggestions()}
            onSelect={handleSuggestionClick}
            className="mt-2"
          />
        )}

        {isProcessing && (
          <div className="flex justify-start">
            <div className="bg-white border rounded-2xl px-4 py-3 shadow-sm">
              <div className="flex gap-1">
                <span className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: "0ms" }} />
                <span className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: "150ms" }} />
                <span className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: "300ms" }} />
              </div>
            </div>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      {/* Input Area - Responsive */}
      <div className="bg-white border-t p-3 sm:p-4 flex-shrink-0">
        <div className="max-w-3xl mx-auto">
          {/* Controls Row - Responsive */}
          <div className="flex flex-wrap items-center gap-2 sm:gap-3">
            {/* Mic Button */}
            <button
              onClick={isRecording ? stopRecording : startRecording}
              disabled={isProcessing || isAudioPlaying}
              className={`w-12 h-12 sm:w-14 sm:h-14 rounded-full flex items-center justify-center transition-all flex-shrink-0 ${isRecording
                ? "bg-red-500 hover:bg-red-600 animate-pulse"
                : isAudioPlaying
                  ? "recording-disabled bg-gray-400"
                  : "bg-gradient-to-br from-green-600 to-emerald-600 hover:from-green-700 hover:to-emerald-700"
                } text-white disabled:opacity-50 shadow-lg`}
              title={isAudioPlaying ? "AI is speaking..." : isRecording ? "Stop Recording" : "Start Recording"}
            >
              {isRecording ? (
                <svg className="w-5 h-5 sm:w-6 sm:h-6" fill="currentColor" viewBox="0 0 24 24">
                  <rect x="6" y="6" width="12" height="12" rx="2" />
                </svg>
              ) : (
                <svg className="w-5 h-5 sm:w-6 sm:h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                    d="M19 11a7 7 0 01-7 7m0 0a7 7 0 01-7-7m7 7v4m0 0H8m4 0h4m-4-8a3 3 0 01-3-3V5a3 3 0 116 0v6a3 3 0 01-3 3z" />
                </svg>
              )}
            </button>

            {/* Voice Controls - Inline on mobile */}
            {isAudioPlaying && (
              <div className="flex-shrink-0">
                <VoiceControls
                  isPlaying={isAudioPlaying}
                  onPauseResume={pauseResumeAudio}
                  volume={audioVolume}
                  onVolumeChange={handleVolumeChange}
                  showVolumeControl={false}
                />
              </div>
            )}

            {/* Text Input - Takes remaining space */}
            <div className="flex-1 flex items-center gap-2 min-w-0">
              <input
                type="text" value={inputText} onChange={(e) => setInputText(e.target.value)}
                onKeyDown={(e) => e.key === "Enter" && sendMessage(inputText)}
                placeholder={isRecording ? "Recording..." : "Type message..."}
                disabled={isRecording || isProcessing}
                className="flex-1 min-w-0 px-3 sm:px-4 py-2 sm:py-3 text-sm sm:text-base border rounded-full focus:ring-2 focus:ring-green-500 focus:border-green-500 disabled:opacity-50"
              />
              <button
                onClick={() => sendMessage(inputText)}
                disabled={!inputText.trim() || isProcessing || wsStatus !== "connected"}
                className="px-3 sm:px-5 py-2 sm:py-3 bg-green-600 text-white rounded-full text-sm sm:text-base hover:bg-green-700 disabled:opacity-50 transition flex-shrink-0"
              >
                <span className="hidden sm:inline">Send</span>
                <svg className="w-5 h-5 sm:hidden" fill="currentColor" viewBox="0 0 24 24">
                  <path d="M2.01 21L23 12 2.01 3 2 10l15 2-15 2z" />
                </svg>
              </button>
            </div>
          </div>
          {isRecording && <p className="text-center text-xs sm:text-sm text-red-500 mt-2">🔴 Recording... Click to stop</p>}
        </div>
      </div>
    </div>
  );
}

