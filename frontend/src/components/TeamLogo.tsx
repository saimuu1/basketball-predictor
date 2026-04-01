interface TeamLogoProps {
  name: string;
  logoUrl?: string | null;
  size?: number;
  className?: string;
}

export default function TeamLogo({ name, logoUrl, size = 28, className = '' }: TeamLogoProps) {
  const initial = name.trim().charAt(0).toUpperCase();

  if (logoUrl) {
    return (
      <img
        src={logoUrl}
        alt={`${name} logo`}
        width={size}
        height={size}
        className={`object-contain flex-shrink-0 ${className}`}
        onError={(e) => {
          // Fall back to initials if image fails to load
          const parent = (e.target as HTMLImageElement).parentElement;
          if (parent) {
            (e.target as HTMLImageElement).style.display = 'none';
            const fallback = parent.querySelector('.logo-fallback');
            if (fallback) (fallback as HTMLElement).style.display = 'flex';
          }
        }}
        style={{ width: size, height: size }}
      />
    );
  }

  return (
    <div
      className={`flex-shrink-0 rounded-full flex items-center justify-center font-bold text-xs bg-gray-100 text-gray-600 ${className}`}
      style={{ width: size, height: size }}
    >
      {initial}
    </div>
  );
}
