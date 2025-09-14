import React, { useState } from 'react';
import {
  Breadcrumb,
  BreadcrumbItem,
  BreadcrumbButton,
  BreadcrumbDivider,
  Input,
  Button,
} from '@fluentui/react-components';
import {
  Search24Regular,
  ChevronRight24Regular,
  Home24Regular,
  Dismiss24Regular,
} from '@fluentui/react-icons';

interface BreadcrumbBarProps {
  currentPath: string;
  searchQuery: string;
  isSearching: boolean;
  onNavigate: (path: string) => void;
  onSearch: (query: string, searchType: 'text' | 'image') => void;
  onClearSearch: () => void;
}

export const BreadcrumbBar: React.FC<BreadcrumbBarProps> = ({
  currentPath,
  searchQuery,
  isSearching,
  onNavigate,
  onSearch,
  onClearSearch
}) => {
  const [searchInput, setSearchInput] = useState(searchQuery);
  const [searchType, setSearchType] = useState<'text' | 'image'>('text');
  
  const pathParts = currentPath.split('/').filter(part => part);
  
  const handleSearchSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (searchInput.trim()) {
      onSearch(searchInput.trim(), searchType);
    }
  };

  const handleClearSearch = () => {
    setSearchInput('');
    onClearSearch();
  };

  const buildPathUpTo = (index: number): string => {
    if (index === 0 && pathParts[0]?.includes(':')) {
      return pathParts[0] + '/';
    }
    return pathParts.slice(0, index + 1).join('/');
  };

  return (
    <div className="bg-background border-b border-border px-3 py-2">
      <div className="flex items-center gap-3">
        <div className="flex-1 flex items-center min-w-0">
          {isSearching ? (
            <div className="flex items-center gap-2 text-sm">
              <Search24Regular className="w-4 h-4 text-muted-foreground flex-shrink-0" />
              <span className="text-muted-foreground">Search results for</span>
              <span className="font-medium">"{searchQuery}"</span>
              <Button
                appearance="subtle"
                size="small"
                icon={<Dismiss24Regular />}
                onClick={handleClearSearch}
                className="ml-2"
              />
            </div>
          ) : (
            <Breadcrumb>
              <BreadcrumbItem>
                <BreadcrumbButton
                  icon={<Home24Regular />}
                  onClick={() => onNavigate('C:/')}
                  className="flex items-center gap-1"
                >
                  This PC
                </BreadcrumbButton>
              </BreadcrumbItem>
              
              {pathParts.map((part, index) => (
                <React.Fragment key={index}>
                  <BreadcrumbDivider>
                    <ChevronRight24Regular className="w-3 h-3" />
                  </BreadcrumbDivider>
                  <BreadcrumbItem>
                    <BreadcrumbButton
                      onClick={() => onNavigate(buildPathUpTo(index))}
                      current={index === pathParts.length - 1}
                      className={index === pathParts.length - 1 ? 'font-medium' : ''}
                    >
                      {part.replace(':', '')}
                    </BreadcrumbButton>
                  </BreadcrumbItem>
                </React.Fragment>
              ))}
            </Breadcrumb>
          )}
        </div>
        
        <form onSubmit={handleSearchSubmit} className="flex items-center gap-2">
          <div className="flex items-center gap-2">
            <select
              value={searchType}
              onChange={(e) => setSearchType(e.target.value as 'text' | 'image')}
              className="w-24 px-2 py-1 border border-gray-300 rounded text-sm"
            >
              <option value="text">Text</option>
              <option value="image">Image</option>
            </select>
            
            <Input
              placeholder={searchType === 'text' ? "Search text content..." : "Describe an image (e.g., 'a cat', 'a dog')..."}
              value={searchInput}
              onChange={(e) => setSearchInput(e.target.value)}
              contentBefore={<Search24Regular className="w-4 h-4 text-muted-foreground" />}
              className="w-64"
            />
          </div>
        </form>
      </div>
    </div>
  );
};