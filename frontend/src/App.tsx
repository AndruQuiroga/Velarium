import { BrowserRouter as Router, Routes, Route, Link } from 'react-router-dom';
import ServerList from './components/ServerList';

function App() {
  return (
    <Router>
      <div className="min-h-screen flex flex-col">
        <nav className="navbar bg-base-100 shadow mb-4">
          <div className="container mx-auto">
            <Link to="/" className="btn btn-ghost normal-case text-xl">Velarium</Link>
          </div>
        </nav>
        <main className="container mx-auto flex-1 p-4">
          <Routes>
            <Route path="/" element={<ServerList />} />
          </Routes>
        </main>
      </div>
    </Router>
  );
}

export default App;
