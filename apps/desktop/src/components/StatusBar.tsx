import React from 'react';
import { fileAPI, FileSystemItem } from '../lib/api';

interface StatusBarProps {
  totalItems: number;
  selectedItems: string[];
  allItems: FileSystemItem[];
}

export const StatusBar: React.FC<StatusBarProps> = ({
  totalItems,
  selectedItems,
  allItems
}) => {
  const selectedCount = selectedItems.length;
  
  const calculateSelectedSize = () => {
    if (selectedCount === 0) return 0;
    
    return allItems
      .filter(item => selectedItems.includes(item.path))
      .reduce((total, item) => total + (item.type === 'file' ? item.size : 0), 0);
  };

  const selectedSize = calculateSelectedSize();

  const getStatusText = () => {
    if (selectedCount === 0) {
      return `${totalItems} item${totalItems !== 1 ? 's' : ''}`;
    }
    
    const sizeText = selectedSize > 0 ? ` (${fileAPI.formatFileSize(selectedSize)})` : '';
    return `${selectedCount} of ${totalItems} item${totalItems !== 1 ? 's' : ''} selected${sizeText}`;
  };

  return (
    <div className="bg-explorer-header border-t border-border px-3 py-1">
      <div className="flex items-center justify-between text-sm text-muted-foreground">
        <span>{getStatusText()}</span>
        
        <div className="flex items-center gap-4">
          {selectedCount > 0 && selectedSize > 0 && (
            <span>Total size: {fileAPI.formatFileSize(selectedSize)}</span>
          )}
          {/* Additional status items can be added here */}
        </div>
      </div>
    </div>
  );
};