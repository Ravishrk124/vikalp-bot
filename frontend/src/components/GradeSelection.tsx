"use client";

import React from "react";

interface GradeSelectionProps {
  onSelectGrade: (grade: string) => void;
  selectedGrade: string | null;
}

const GRADES = [
  { id: "Nursery", label: "Nursery", icon: "🎒", color: "bg-pink-500" },
  { id: "LKG", label: "LKG", icon: "🧒", color: "bg-orange-500" },
  { id: "UKG", label: "UKG", icon: "👦", color: "bg-amber-500" },
  { id: "Grade 1", label: "Grade 1", icon: "1", color: "bg-lime-500" },
  { id: "Grade 2", label: "Grade 2", icon: "2", color: "bg-green-500" },
  { id: "Grade 3", label: "Grade 3", icon: "3", color: "bg-emerald-500" },
  { id: "Grade 4", label: "Grade 4", icon: "4", color: "bg-teal-500" },
  { id: "Grade 5", label: "Grade 5", icon: "5", color: "bg-cyan-500" },
  { id: "Grade 6", label: "Grade 6", icon: "6", color: "bg-blue-500" },
  { id: "Grade 7", label: "Grade 7", icon: "7", color: "bg-indigo-500" },
  { id: "Grade 8", label: "Grade 8", icon: "8", color: "bg-violet-500" },
  { id: "Grade 9", label: "Grade 9", icon: "9", color: "bg-purple-500" },
  { id: "Grade 10", label: "Grade 10", icon: "10", color: "bg-fuchsia-500" },
  { id: "Grade 11", label: "Grade 11", icon: "📚", color: "bg-rose-500" },
  { id: "Grade 12", label: "Grade 12", icon: "🎓", color: "bg-red-500" },
];

export default function GradeSelection({ onSelectGrade, selectedGrade }: GradeSelectionProps) {
  return (
    <div className="grid grid-cols-3 sm:grid-cols-4 md:grid-cols-5 gap-2 sm:gap-3">
      {GRADES.map((grade) => (
        <button
          key={grade.id}
          onClick={() => onSelectGrade(grade.id)}
          className={`
            p-2 sm:p-3 lg:p-4 rounded-lg sm:rounded-xl text-white transition-all duration-150
            ${grade.color}
            ${selectedGrade === grade.id
              ? "ring-2 sm:ring-4 ring-green-400 ring-offset-1 sm:ring-offset-2 scale-105"
              : "hover:scale-105 hover:shadow-lg active:scale-95"
            }
          `}
        >
          <div className="w-6 h-6 sm:w-8 lg:w-10 sm:h-8 lg:h-10 mx-auto mb-1 sm:mb-2 bg-white/20 rounded-md sm:rounded-lg flex items-center justify-center text-xs sm:text-sm lg:text-lg font-bold">
            {grade.icon}
          </div>
          <div className="text-[10px] sm:text-xs lg:text-sm font-semibold text-center truncate">{grade.label}</div>
        </button>
      ))}
    </div>
  );
}
