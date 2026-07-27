import React, { FormEvent, useCallback, useEffect, useState } from 'react';
import { useRouter } from 'next/router';

import CredentialModal from '@/components/CredentialModal';
import { apiUrl, readJson } from '@/lib/api';
import type { Game, IntegrationStatus } from '@/types/game';


const authenticatedHeaders = () => ({
  'Content-Type': 'application/json',
  Authorization: `Bearer ${localStorage.getItem('token') ?? ''}`,
});


const Home = () => {
  const router = useRouter();
  const [searchTerm, setSearchTerm] = useState('');
  const [games, setGames] = useState<Game[]>([]);
  const [dropdownOpen, setDropdownOpen] = useState(false);
  const [wishlist, setWishlist] = useState<string[]>([]);
  const [username, setUsername] = useState('');
  const [rapidApiStatus, setRapidApiStatus] = useState<IntegrationStatus | null>(null);

  useEffect(() => {
    const load = async () => {
      const [statusResponse, gamesResponse, wishlistResponse, userResponse] = await Promise.all([
        fetch(apiUrl('/data/integration-status')),
        fetch(apiUrl('/data/games'), { headers: authenticatedHeaders() }),
        fetch(apiUrl('/data/favorite'), { headers: authenticatedHeaders() }),
        fetch(apiUrl('/data/user_data'), { headers: authenticatedHeaders() }),
      ]);

      const status = await readJson<IntegrationStatus>(statusResponse);
      if (statusResponse.ok && status?.source === 'fixture') setRapidApiStatus(status);

      const loadedGames = await readJson<Game[]>(gamesResponse);
      if (gamesResponse.ok && Array.isArray(loadedGames)) setGames(loadedGames);

      const loadedWishlist = await readJson<string[]>(wishlistResponse);
      if (wishlistResponse.ok && Array.isArray(loadedWishlist)) setWishlist(loadedWishlist);

      const loadedUser = await readJson<{ message?: string }>(userResponse);
      if (userResponse.ok && loadedUser?.message) setUsername(loadedUser.message);
    };
    void load();
  }, []);

  const handleAddToWishlist = async (gameId: string) => {
    const response = await fetch(apiUrl(`/data/favorite/add/${gameId}`), {
      method: 'POST',
      headers: authenticatedHeaders(),
    });
    if (response.ok) {
      setWishlist((current) => current.includes(gameId) ? current : [...current, gameId]);
    }
  };

  const handleRemoveFromWishlist = async (gameId: string) => {
    const response = await fetch(apiUrl(`/data/favorite/remove/${gameId}`), {
      method: 'DELETE',
      headers: authenticatedHeaders(),
    });
    if (response.ok) setWishlist((current) => current.filter((id) => id !== gameId));
  };

  const handleSearch = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    const query = new URLSearchParams({ q: searchTerm });
    const response = await fetch(apiUrl(`/data/search_games?${query}`), {
      headers: authenticatedHeaders(),
    });
    const results = await readJson<Game[]>(response);
    if (response.ok && Array.isArray(results)) setGames(results);
  };

  const closeRapidApiModal = useCallback(() => setRapidApiStatus(null), []);
  const fallbackDescription = rapidApiStatus?.fallbackReason === 'live_api_unavailable'
    ? 'Las credenciales están configuradas, pero Steam2/RapidAPI no ha respondido correctamente. La aplicación ha cargado automáticamente el conjunto local para seguir funcionando.'
    : 'No se ha configurado RapidAPI. La aplicación sigue funcionando con el conjunto local de juegos; para consultar datos en vivo configura la siguiente variable en .env y recrea los servicios.';

  return (
    <div className="min-h-screen bg-gray-900">
      <header className="fixed top-0 z-20 flex w-full items-center justify-between bg-gray-950 p-4 text-white">
        <div className="flex items-center">
          <img alt="Logo" className="mr-3 h-10 w-auto" src="/steam-logo.png" />
          <h1 className="text-xl">GameShop</h1>
        </div>
        <form className="relative flex w-1/2 items-center" onSubmit={handleSearch}>
          <input className="flex-grow rounded-md border p-2 pl-10 text-black" onChange={(event) => setSearchTerm(event.target.value)} placeholder="Buscar..." type="text" value={searchTerm} />
          <img alt="Buscar" className="absolute left-2 h-4 w-4" src="/lupa.png" />
        </form>
        <div className="relative">
          <button aria-label="Abrir menú de usuario" onClick={() => setDropdownOpen((open) => !open)} type="button">
            <img alt="Perfil de usuario" className="h-10 w-10" src="/user-profile.jpg" />
          </button>
          {dropdownOpen && (
            <div className="absolute right-0 z-10 mt-2 w-48 overflow-hidden rounded-md border border-gray-700 bg-gray-950 shadow-xl">
              <p className="px-4 py-2 text-white">Sesión de {username}</p>
              <button className="block w-full px-4 py-2 text-left text-white hover:bg-gray-800" onClick={() => router.push('/favorites')} type="button">Deseados</button>
              <button className="block w-full bg-red-500 px-4 py-2 text-left text-white hover:bg-red-600" onClick={() => { localStorage.removeItem('token'); void router.push('/login'); }} type="button">Cerrar sesión</button>
            </div>
          )}
        </div>
      </header>
      <main className="mx-auto max-w-7xl px-6 pt-20 sm:px-8">
        <h2 className="py-8 text-center text-4xl text-white">Juegos destacados</h2>
        <ul className="mx-auto mt-10 grid grid-cols-1 gap-8 sm:grid-cols-2 lg:grid-cols-4" role="list">
          {games.map((game) => (
            <li className="rounded-lg bg-gray-800 p-6" key={game.appId}>
              <a href={game.url} rel="noreferrer" target="_blank">
                <img alt={game.title} className="aspect-[3/2] w-full rounded object-contain object-center" src={game.imgUrl} />
                <h3 className="mt-6 text-xl font-semibold leading-8 tracking-tight text-white">{game.title}</h3>
                <p className="text-base leading-7 text-gray-300">Valoración positiva: {game.reviewSummary ?? 'No disponible'}</p>
                <div className="mt-2 flex items-center justify-between">
                  <div className="text-base leading-7 text-white">
                    {game.discountedPrice ? (
                      <><p>Precio original: <span className="line-through">{game.originalPrice}</span></p><p>Precio rebajado: {game.discountedPrice}</p></>
                    ) : <p>Precio: {game.originalPrice ?? 'No disponible'}</p>}
                  </div>
                  <button
                    aria-label={wishlist.includes(game.appId) ? `Quitar ${game.title} de deseados` : `Añadir ${game.title} a deseados`}
                    onClick={(event) => {
                      event.preventDefault();
                      event.stopPropagation();
                      void (wishlist.includes(game.appId) ? handleRemoveFromWishlist(game.appId) : handleAddToWishlist(game.appId));
                    }}
                    type="button"
                  >
                    <img alt="" className="h-6 w-6" src={wishlist.includes(game.appId) ? '/Estrella_llena.png' : '/Estrella_vacia.png'} />
                  </button>
                </div>
              </a>
            </li>
          ))}
        </ul>
      </main>
      <CredentialModal
        description={fallbackDescription}
        missingCredentials={rapidApiStatus?.missingCredentials}
        onClose={closeRapidApiModal}
        open={rapidApiStatus !== null}
        title="Datos locales de RapidAPI en uso"
      />
    </div>
  );
};

export default Home;
