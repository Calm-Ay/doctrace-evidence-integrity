import React, { useRef, useState } from 'react';
import { UploadCloud } from 'lucide-react';
import { cn } from '../lib/utils';

export function DropZone({ onFile, label }) {
  const [isDragOver, setIsDragOver] = useState(false);
  const fileInputRef = useRef(null);

  const handleDragOver = (e) => {
    e.preventDefault();
    setIsDragOver(true);
  };

  const handleDragLeave = (e) => {
    e.preventDefault();
    setIsDragOver(false);
  };

  const handleDrop = (e) => {
    e.preventDefault();
    setIsDragOver(false);
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      onFile(e.dataTransfer.files[0]);
    }
  };

  const handleClick = () => {
    if (fileInputRef.current) {
      fileInputRef.current.click();
    }
  };

  const handleChange = (e) => {
    if (e.target.files && e.target.files.length > 0) {
      onFile(e.target.files[0]);
    }
  };

  return (
    <div
      onDragOver={handleDragOver}
      onDragLeave={handleDragLeave}
      onDrop={handleDrop}
      onClick={handleClick}
      className={cn(
        "w-full h-48 border-2 border-dashed rounded-xl flex flex-col items-center justify-center cursor-pointer transition-colors bg-white/60",
        isDragOver ? "border-cyan bg-cyan/5" : "border-silver hover:border-cyan hover:bg-cyan/5"
      )}
    >
      <input
        type="file"
        ref={fileInputRef}
        onChange={handleChange}
        className="hidden"
      />
      <UploadCloud className={cn("w-12 h-12 mb-3", isDragOver ? "text-cyan" : "text-muted-ink")} />
      <span className={cn("font-medium", isDragOver ? "text-cyan" : "text-ink")}>{label}</span>
    </div>
  );
}
