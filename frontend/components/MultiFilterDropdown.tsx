'use client';

import { useState } from 'react';
import { ChevronDown, X, Search } from 'lucide-react';

interface FilterOption {
  key: string;
  label: string;
  type: 'text' | 'number' | 'date' | 'select' | 'checkbox';
  options?: Array<{ label: string; value: string }>;
  placeholder?: string;
}

interface MultiFilterDropdownProps {
  filters: FilterOption[];
  onFilterChange: (filters: Record<string, string>) => void;
  onReset: () => void;
}

export const MultiFilterDropdown = ({
  filters,
  onFilterChange,
  onReset
}: MultiFilterDropdownProps) => {
  const [isOpen, setIsOpen] = useState(false);
  const [filterValues, setFilterValues] = useState<Record<string, string>>({});
  const [activeFilters, setActiveFilters] = useState<number>(0);

  const handleFilterChange = (key: string, value: string) => {
    const updated = { ...filterValues, [key]: value };
    setFilterValues(updated);
    
    // Count active filters
    const count = Object.values(updated).filter(v => v).length;
    setActiveFilters(count);
  };

  const handleApply = () => {
    // Remove empty values
    const cleanFilters = Object.fromEntries(
      Object.entries(filterValues).filter(([_, v]) => v)
    );
    onFilterChange(cleanFilters);
    setIsOpen(false);
  };

  const handleReset = () => {
    setFilterValues({});
    setActiveFilters(0);
    onReset();
    setIsOpen(false);
  };

  return (
    <div className="relative">
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="flex items-center gap-2 px-4 py-2 bg-card border border-white/10 rounded-xl hover:bg-muted transition shadow-lg font-bold text-foreground"
      >
        <Search size={16} className="text-primary" />
        <span className="text-sm">Filters</span>
        {activeFilters > 0 && (
          <span className="bg-primary text-primary-foreground text-[10px] font-black rounded-full w-5 h-5 flex items-center justify-center shadow-inner">
            {activeFilters}
          </span>
        )}
        <ChevronDown size={16} className={`transition-transform duration-200 ${isOpen ? 'rotate-180' : ''}`} />
      </button>

      {isOpen && (
        <div className="absolute top-full left-0 mt-3 bg-card/95 backdrop-blur-md border border-white/10 rounded-2xl shadow-2xl z-50 w-80 animate-in fade-in zoom-in-95 duration-200">
          <div className="p-6 space-y-5 max-h-[400px] overflow-y-auto custom-scrollbar">
            {filters.map((filter) => (
              <div key={filter.key} className="space-y-2">
                <label className="block text-xs font-bold text-muted-foreground uppercase tracking-wider">
                  {filter.label}
                </label>

                {filter.type === 'select' && filter.options ? (
                  <select
                    value={filterValues[filter.key] || ''}
                    onChange={(e) => handleFilterChange(filter.key, e.target.value)}
                    className="w-full px-4 py-2.5 bg-background border border-border rounded-xl text-sm focus:ring-2 focus:ring-primary/50 outline-none transition-all"
                  >
                    <option value="">{filter.placeholder || 'Select...'}</option>
                    {filter.options.map((opt) => (
                      <option key={opt.value} value={opt.value}>
                        {opt.label}
                      </option>
                    ))}
                  </select>
                ) : filter.type === 'checkbox' ? (
                  <div className="flex items-center gap-3">
                    <input
                      type="checkbox"
                      checked={filterValues[filter.key] === 'true'}
                      onChange={(e) => handleFilterChange(filter.key, e.target.checked ? 'true' : '')}
                      className="w-5 h-5 bg-background border border-border rounded text-primary focus:ring-primary/50"
                    />
                    <span className="text-sm font-medium text-foreground">Active Only</span>
                  </div>
                ) : (
                  <input
                    type={filter.type}
                    value={filterValues[filter.key] || ''}
                    onChange={(e) => handleFilterChange(filter.key, e.target.value)}
                    placeholder={filter.placeholder || 'Enter value...'}
                    className="w-full px-4 py-2.5 bg-background border border-border rounded-xl text-sm focus:ring-2 focus:ring-primary/50 outline-none transition-all"
                  />
                )}
              </div>
            ))}
          </div>

          {/* Actions */}
          <div className="flex gap-3 p-6 bg-muted/20 border-t border-white/5 rounded-b-2xl">
            <button
              onClick={handleReset}
              className="flex-1 px-4 py-2.5 text-sm font-bold border border-white/10 rounded-xl hover:bg-muted transition text-muted-foreground"
            >
              Reset
            </button>
            <button
              onClick={handleApply}
              className="flex-1 px-4 py-2.5 text-sm font-bold bg-primary text-primary-foreground rounded-xl hover:opacity-90 transition shadow-lg"
            >
              Apply Filters
            </button>
          </div>
        </div>
      )}
    </div>
  );
};
