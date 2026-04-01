import { AlertTriangle, RefreshCw } from 'lucide-react';

interface ErrorStateProps {
  message: string;
  onRetry?: () => void;
}

export default function ErrorState({ message, onRetry }: ErrorStateProps) {
  return (
    <div className="flex flex-col items-center justify-center py-12 gap-4 text-center px-6">
      <div className="w-12 h-12 rounded-2xl bg-rose-50 flex items-center justify-center">
        <AlertTriangle size={22} className="text-rose-500" />
      </div>
      <div>
        <p className="text-sm font-semibold text-gray-800">Something went wrong</p>
        <p className="text-xs text-gray-500 mt-1 max-w-xs">{message}</p>
      </div>
      {onRetry && (
        <button
          onClick={onRetry}
          className="flex items-center gap-1.5 text-sm text-blue-600 font-medium hover:text-blue-700 px-4 py-2 rounded-lg hover:bg-blue-50 transition-colors"
        >
          <RefreshCw size={13} />
          Try again
        </button>
      )}
    </div>
  );
}
