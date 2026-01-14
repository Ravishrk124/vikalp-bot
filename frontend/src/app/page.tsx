"use client";

import React, { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import GradeSelection from "../components/GradeSelection";
import CourseSelection from "../components/CourseSelection";
import LeadCaptureModal from "../components/LeadCaptureModal";

type TabType = "school" | "courses";

export default function HomePage() {
  const router = useRouter();
  const [activeTab, setActiveTab] = useState<TabType>("school");
  const [selectedItem, setSelectedItem] = useState<string | null>(null);
  const [showLeadForm, setShowLeadForm] = useState(false);
  const [checkingSession, setCheckingSession] = useState(true);

  // Check for existing valid session on mount
  useEffect(() => {
    const storedSession = localStorage.getItem('vikalp_session');
    if (storedSession) {
      try {
        const session = JSON.parse(storedSession);
        const expiresAt = new Date(session.expires_at);

        // If session is still valid (not expired), redirect to chat
        if (expiresAt > new Date() && session.session_id) {
          router.push(`/chat?session_id=${session.session_id}`);
          return;
        } else {
          // Session expired, clear it
          localStorage.removeItem('vikalp_session');
        }
      } catch (e) {
        // Invalid session data, clear it
        localStorage.removeItem('vikalp_session');
      }
    }
    setCheckingSession(false);
  }, [router]);

  // Show loading while checking session
  if (checkingSession) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <div className="text-center">
          <div className="w-12 h-12 border-4 border-green-600 border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
          <p className="text-gray-600">Checking session...</p>
        </div>
      </div>
    );
  }

  const handleItemSelect = (item: string) => {
    setSelectedItem(item);
    setShowLeadForm(true);
  };

  const handleCloseModal = () => {
    setShowLeadForm(false);
    setSelectedItem(null);
  };

  return (
    <main className="min-h-screen flex flex-col bg-gray-50 overflow-x-hidden">
      {/* Header - Responsive */}
      <header className="bg-white shadow-sm border-b border-gray-200 flex-shrink-0">
        <div className="px-4 sm:px-6 lg:px-8 py-3 flex items-center justify-between">
          <div className="flex items-center gap-2 sm:gap-3">
            <div className="w-8 h-8 sm:w-10 sm:h-10 bg-green-600 rounded-lg flex items-center justify-center">
              <span className="text-white font-bold text-base sm:text-lg">V</span>
            </div>
            <div>
              <h1 className="text-sm sm:text-lg font-bold text-gray-900">Vikalp Online School</h1>
              <p className="text-[10px] sm:text-xs text-green-600 font-medium">CBSE/NIOS Curriculum</p>
            </div>
          </div>
          {/* Contact - Hidden on mobile, visible on tablet+ */}
          <div className="hidden sm:flex items-center gap-4 lg:gap-6 text-xs sm:text-sm">
            <a href="tel:+919910074585" className="flex items-center gap-1.5 text-gray-600 hover:text-green-600 transition">
              📞 <span className="hidden md:inline">+91-</span>9910074585
            </a>
            <a href="mailto:letters@vikalpindia.com" className="hidden lg:flex items-center gap-1.5 text-gray-600 hover:text-green-600 transition">
              ✉️ letters@vikalpindia.com
            </a>
          </div>
          {/* Mobile call button */}
          <a href="tel:+919910074585" className="sm:hidden w-8 h-8 bg-green-100 rounded-full flex items-center justify-center text-green-600">
            📞
          </a>
        </div>
      </header>

      {/* Main Content - Responsive */}
      <div className="flex-1 flex flex-col items-center justify-center px-4 sm:px-6 lg:px-8 py-4 sm:py-6">
        {/* Title - Responsive text sizes */}
        <h2 className="text-lg sm:text-xl lg:text-2xl font-bold text-gray-900 mb-1 text-center">
          Welcome to <span className="text-green-600">Vikalp AI Voice Tutor</span>
        </h2>
        <p className="text-gray-500 text-xs sm:text-sm mb-4 sm:mb-6 text-center max-w-lg">
          Get guidance for admissions, curriculum, fees • Speak in any language!
        </p>

        {/* Tabs - Responsive */}
        <div className="flex bg-white rounded-lg p-1 shadow-sm border border-gray-200 mb-4 sm:mb-6">
          <button
            onClick={() => setActiveTab("school")}
            className={`px-3 sm:px-6 py-1.5 sm:py-2 rounded-md text-xs sm:text-sm font-medium transition-all ${activeTab === "school"
              ? "bg-green-600 text-white"
              : "text-gray-600 hover:bg-gray-100"
              }`}
          >
            🏫 <span className="hidden xs:inline">Accredited </span>School
          </button>
          <button
            onClick={() => setActiveTab("courses")}
            className={`px-3 sm:px-6 py-1.5 sm:py-2 rounded-md text-xs sm:text-sm font-medium transition-all ${activeTab === "courses"
              ? "bg-green-600 text-white"
              : "text-gray-600 hover:bg-gray-100"
              }`}
          >
            📚 <span className="hidden xs:inline">Online </span>Classes
          </button>
        </div>

        {/* Content - Full width on mobile */}
        <div className="w-full max-w-7xl">
          {activeTab === "school" ? (
            <GradeSelection onSelectGrade={handleItemSelect} selectedGrade={selectedItem} />
          ) : (
            <CourseSelection onSelectCourse={handleItemSelect} selectedCourse={selectedItem} />
          )}
        </div>

        {/* Tip */}
        <p className="text-[10px] sm:text-xs text-gray-400 mt-3 sm:mt-4 text-center">
          💡 Select a {activeTab === "school" ? "grade" : "course"} to start a voice conversation
        </p>
      </div>

      {/* Modal */}
      {showLeadForm && selectedItem && (
        <LeadCaptureModal grade={selectedItem} onClose={handleCloseModal} />
      )}

      {/* Footer - Responsive */}
      <footer className="bg-white border-t border-gray-200 flex-shrink-0 py-2 text-center text-[10px] sm:text-xs text-gray-400">
        © 2024 Vikalp Online School • Powered by AI Voice Technology
      </footer>
    </main>
  );
}
