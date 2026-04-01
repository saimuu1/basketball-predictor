interface LoadingStateProps {
  message?: string;
}

export default function LoadingState({ message = 'Loading…' }: LoadingStateProps) {
  return (
    <div className="flex flex-col items-center justify-center py-12 gap-3">
      <div className="relative w-10 h-10">
        <div className="absolute inset-0 rounded-full border-2 border-gray-200" />
        <div className="absolute inset-0 rounded-full border-2 border-t-blue-500 animate-spin" />
      </div>
      <p className="text-sm text-gray-500 font-medium">{message}</p>
    </div>
  );
}
