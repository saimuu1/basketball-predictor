import { BrowserRouter, Routes, Route } from 'react-router-dom';
import Header from './components/Header';
import Home from './pages/Home';
import PredictionPage from './pages/PredictionPage';

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        {/* Prediction page — full screen, no shared header/footer */}
        <Route path="/predict/:gameId" element={<PredictionPage />} />

        {/* Main layout with header */}
        <Route
          path="*"
          element={
            <div className="min-h-screen bg-gray-50 flex flex-col">
              <Header />
              <div className="flex-1">
                <Home />
              </div>
              <footer className="py-4 text-center text-xs text-gray-400 border-t border-gray-100 bg-white">
                College Basketball Predictor · D1 only · Predictions are for informational purposes only
              </footer>
            </div>
          }
        />
      </Routes>
    </BrowserRouter>
  );
}
