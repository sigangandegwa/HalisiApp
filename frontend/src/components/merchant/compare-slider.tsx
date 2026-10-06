"use client";

import { useState, useRef, useEffect, KeyboardEvent } from "react";
import { MoveHorizontal } from "lucide-react";

export function CompareSlider({ official, suspect }: { official: string; suspect: string }) {
  const [position, setPosition] = useState(50);
  const [isDiff, setIsDiff] = useState(false);
  const containerRef = useRef<HTMLDivElement>(null);

  const handlePointerMove = (e: React.PointerEvent | PointerEvent) => {
    if (!containerRef.current || e.buttons !== 1) return;
    const rect = containerRef.current.getBoundingClientRect();
    const x = Math.max(0, Math.min(e.clientX - rect.left, rect.width));
    setPosition((x / rect.width) * 100);
  };

  const handleKeyDown = (e: KeyboardEvent) => {
    if (e.key === "ArrowLeft") setPosition(Math.max(0, position - 5));
    if (e.key === "ArrowRight") setPosition(Math.min(100, position + 5));
  };

  useEffect(() => {
    const el = containerRef.current;
    if (!el) return;
    const handleMove = (e: PointerEvent) => handlePointerMove(e);
    el.addEventListener("pointermove", handleMove);
    return () => el.removeEventListener("pointermove", handleMove);
  }, []);

  return (
    <div className="space-y-4">
      <div 
        ref={containerRef}
        className="relative w-full aspect-square bg-bg-2 rounded-sm overflow-hidden touch-none select-none"
        tabIndex={0}
        onKeyDown={handleKeyDown}
        aria-valuenow={position}
        role="slider"
      >
        <img 
          src={suspect} 
          alt="Suspect avatar" 
          className="absolute inset-0 w-full h-full object-contain pointer-events-none" 
          style={{ mixBlendMode: isDiff ? "difference" : "normal" }}
        />
        
        <div 
          className="absolute inset-0 pointer-events-none"
          style={{ clipPath: `inset(0 ${100 - position}% 0 0)` }}
        >
           <img 
             src={official} 
             alt="Official logo" 
             className="w-full h-full object-contain bg-bg-2" 
           />
        </div>
        
        {/* Slider handle */}
        <div 
          className="absolute top-0 bottom-0 w-0.5 bg-fg cursor-ew-resize flex items-center justify-center pointer-events-none"
          style={{ left: `${position}%`, transform: 'translateX(-50%)' }}
        >
          <div className="w-8 h-8 bg-fg rounded-full flex items-center justify-center text-bg shadow-sm">
             <MoveHorizontal className="w-4 h-4" />
          </div>
        </div>
      </div>
      
      <div className="flex items-center justify-between">
         <span className="type-caption text-fg-2">Official logo</span>
         <label className="flex items-center gap-2 type-caption text-fg cursor-pointer">
            <input 
              type="checkbox" 
              checked={isDiff} 
              onChange={e => setIsDiff(e.target.checked)} 
              className="accent-fg"
            />
            Difference mode
         </label>
         <span className="type-caption text-fg-2">Suspect avatar</span>
      </div>
    </div>
  );
}
