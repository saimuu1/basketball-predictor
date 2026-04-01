import { formatPercent } from '../utils/format';

interface ProbabilityBarProps {
  teamAName: string;
  teamBName: string;
  teamAProb: number;
  teamBProb: number;
}

export default function ProbabilityBar({
  teamAName,
  teamBName,
  teamAProb,
  teamBProb,
}: ProbabilityBarProps) {
  const aPercent = Math.round(teamAProb * 100);
  const bPercent = Math.round(teamBProb * 100);

  return (
    <div>
      {/* Labels */}
      <div className="flex justify-between items-center mb-2">
        <div className="flex items-center gap-1.5">
          <div className="w-2.5 h-2.5 rounded-full bg-blue-500" />
          <span className="text-sm font-medium text-gray-700 truncate max-w-[110px]">
            {teamAName}
          </span>
        </div>
        <div className="flex items-center gap-1.5">
          <span className="text-sm font-medium text-gray-700 truncate max-w-[110px] text-right">
            {teamBName}
          </span>
          <div className="w-2.5 h-2.5 rounded-full bg-orange-400" />
        </div>
      </div>

      {/* Bar */}
      <div className="relative h-3 rounded-full bg-gray-100 overflow-hidden">
        <div
          className="absolute left-0 top-0 h-full bg-blue-500 transition-all duration-700 ease-out rounded-l-full"
          style={{ width: `${aPercent}%` }}
        />
        <div
          className="absolute right-0 top-0 h-full bg-orange-400 transition-all duration-700 ease-out rounded-r-full"
          style={{ width: `${bPercent}%` }}
        />
      </div>

      {/* Percentages */}
      <div className="flex justify-between mt-1.5">
        <span className="text-lg font-bold text-blue-600">{formatPercent(teamAProb)}</span>
        <span className="text-lg font-bold text-orange-500">{formatPercent(teamBProb)}</span>
      </div>
    </div>
  );
}
