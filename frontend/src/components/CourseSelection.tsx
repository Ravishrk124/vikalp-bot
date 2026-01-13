"use client";

import React from "react";

interface CourseSelectionProps {
    onSelectCourse: (course: string) => void;
    selectedCourse: string | null;
}

const COURSES = [
    { id: "Indian Languages", label: "Indian Languages", icon: "🇮🇳", color: "bg-red-500" },
    { id: "Foreign Languages", label: "Foreign Languages", icon: "🌍", color: "bg-teal-500" },
    { id: "Math & Science", label: "Math & Science", icon: "🔬", color: "bg-pink-500" },
    { id: "1-to-1 Math", label: "1-to-1 Math", icon: "📐", color: "bg-green-500" },
    { id: "Computer Science", label: "Computer Science", icon: "💻", color: "bg-blue-500" },
    { id: "Coding", label: "Coding", icon: "👨‍💻", color: "bg-orange-500" },
    { id: "Classical Dance", label: "Classical Dance", icon: "💃", color: "bg-amber-500" },
    { id: "Classical Music", label: "Classical Music", icon: "🎵", color: "bg-purple-500" },
    { id: "Phonics", label: "Phonics", icon: "🔤", color: "bg-violet-500" },
    { id: "Public Speaking", label: "Public Speaking", icon: "🎤", color: "bg-cyan-500" },
    { id: "Yoga", label: "Yoga", icon: "🧘", color: "bg-rose-500" },
    { id: "Hobby Classes", label: "Hobby Classes", icon: "🎨", color: "bg-emerald-500" },
];

export default function CourseSelection({ onSelectCourse, selectedCourse }: CourseSelectionProps) {
    return (
        <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-2 sm:gap-3">
            {COURSES.map((course) => (
                <button
                    key={course.id}
                    onClick={() => onSelectCourse(course.id)}
                    className={`
            flex items-center gap-2 sm:gap-3 p-2 sm:p-3 lg:p-4 rounded-lg sm:rounded-xl text-white transition-all duration-150
            ${course.color}
            ${selectedCourse === course.id
                            ? "ring-2 sm:ring-4 ring-green-400 ring-offset-1 sm:ring-offset-2 scale-105"
                            : "hover:scale-105 hover:shadow-lg active:scale-95"
                        }
          `}
                >
                    <div className="w-8 h-8 sm:w-10 sm:h-10 bg-white/20 rounded-md sm:rounded-lg flex items-center justify-center text-base sm:text-xl flex-shrink-0">
                        {course.icon}
                    </div>
                    <span className="text-[10px] sm:text-xs lg:text-sm font-semibold text-left leading-tight">{course.label}</span>
                </button>
            ))}
        </div>
    );
}
