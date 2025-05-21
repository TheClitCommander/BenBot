import React from 'react';
import { ArrowUpRight, ArrowDownRight, HelpCircle } from 'lucide-react';

interface KPICardProps {
  title: string;
  value: string | number;
  change?: number;
  icon?: React.ReactNode;
  tooltip?: string;
  onClick?: () => void;
  loading?: boolean;
}

const KPICard: React.FC<KPICardProps> = ({
  title,
  value,
  change,
  icon,
  tooltip,
  onClick,
  loading = false,
}) => {
  return (
    <div 
      className={`bg-white rounded-lg shadow-sm border border-gray-200 p-4 h-full flex flex-col transition-all ${
        onClick ? 'cursor-pointer hover:shadow-md hover:border-blue-300' : ''
      }`}
      onClick={onClick}
    >
      {loading ? (
        <div className="animate-pulse h-full flex flex-col">
          <div className="flex justify-between items-start">
            <div className="h-4 bg-gray-200 rounded w-24 mb-2"></div>
            <div className="h-6 w-6 rounded-full bg-gray-200"></div>
          </div>
          <div className="h-8 bg-gray-200 rounded w-20 mt-2"></div>
          <div className="h-4 bg-gray-200 rounded w-16 mt-2"></div>
        </div>
      ) : (
        <>
          <div className="flex justify-between items-start mb-2">
            <div className="flex items-center">
              <h3 className="text-gray-500 text-sm font-medium">{title}</h3>
              {tooltip && (
                <div className="ml-1 text-gray-400 cursor-help" title={tooltip}>
                  <HelpCircle size={14} />
                </div>
              )}
            </div>
            {icon && (
              <div className="text-blue-500 bg-blue-50 p-2 rounded-full">
                {icon}
              </div>
            )}
          </div>
          
          <div className="mt-1">
            <p className="text-2xl font-bold text-gray-900">
              {typeof value === 'number' && !isNaN(value) ? value.toLocaleString() : value}
            </p>
          </div>
          
          {change !== undefined && (
            <div className="mt-1 flex items-center">
              {change > 0 ? (
                <span className="inline-flex items-center text-green-600 text-sm">
                  <ArrowUpRight className="mr-1" size={14} />
                  +{change.toFixed(2)}%
                </span>
              ) : change < 0 ? (
                <span className="inline-flex items-center text-red-600 text-sm">
                  <ArrowDownRight className="mr-1" size={14} />
                  {change.toFixed(2)}%
                </span>
              ) : (
                <span className="inline-flex items-center text-gray-500 text-sm">
                  0.00%
                </span>
              )}
            </div>
          )}
        </>
      )}
    </div>
  );
};

export default KPICard; 