import { useEffect, useState } from 'react';
import axios from 'axios';

interface Server {
  id: string;
  name: string;
  status: string;
}

export default function ServerList() {
  const [servers, setServers] = useState<Server[]>([]);

  useEffect(() => {
    axios
      .get('/api/servers')
      .then((res) => setServers(res.data.servers ?? []))
      .catch(() => setServers([]));
  }, []);

  return (
    <div>
      <h2 className="text-2xl font-bold mb-4">Servers</h2>
      <ul className="space-y-2">
        {servers.map((server) => (
          <li key={server.id} className="p-4 bg-base-100 rounded shadow flex justify-between items-center">
            <div>
              <p className="font-medium">{server.name}</p>
              <p className="text-sm opacity-70">{server.status}</p>
            </div>
            <div className="space-x-2">
              <button className="btn btn-sm btn-success">Start</button>
              <button className="btn btn-sm btn-error">Stop</button>
            </div>
          </li>
        ))}
        {servers.length === 0 && <li className="text-center text-sm opacity-70">No servers yet.</li>}
      </ul>
    </div>
  );
}
