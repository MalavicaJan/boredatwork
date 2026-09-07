import { BrowserRouter, Routes, Route } from "react-router-dom";

import { AuthProvider } from "./api/auth";
import Home from "./pages/Home";
import Wordly from "./games/wordly/Wordly.tsx";
import Sequence from "./games/sequence/Sequence.tsx";
import Sudoku from "./games/sudoku/Sudoku.tsx";
import Memory from "./games/memory/Memory.tsx";
import WordlyPractice from "./games/wordly/WordlyPractice.tsx";
import Blackout from "./games/blackout/Blackout.tsx";
import Login from "./pages/Login";
import Register from "./pages/Register";
import Progress from "./pages/Progress";


function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/wordly" element={<Wordly />} />
          <Route path="/sequence" element={<Sequence />} />
          <Route path="/sudoku" element={<Sudoku />} />
          <Route path="/memory" element={<Memory />} />
          <Route path="/wordly-practice" element={<WordlyPractice />} />
          <Route path="/blackout" element={<Blackout />} />
          <Route path="/login" element={<Login />} />
          <Route path="/register" element={<Register />} />
          <Route path="/progress" element={<Progress />} />

        </Routes>
      </AuthProvider>
    </BrowserRouter>
  );
}

export default App;