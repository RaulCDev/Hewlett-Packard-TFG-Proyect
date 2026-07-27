import React, { FormEvent, useEffect, useState } from 'react';
import { useRouter } from 'next/router';

import { apiUrl, readJson } from '@/lib/api';
import type { Game } from '@/types/game';


const authHeaders = () => ({
  'Content-Type': 'application/json',
  Authorization: `Bearer ${localStorage.getItem('token') ?? ''}`,
});


const Favorites = () => {
  const router = useRouter();
  const [searchTerm, setSearchTerm] = useState('');
  const [games, setGames] = useState<Game[]>([]);
  const [allGames, setAllGames] = useState<Game[]>([]);
  const [dropdownOpen, setDropdownOpen] = useState(false);
  const [wishlist, setWishlist] = useState<string[]>([]);
  const [username, setUsername] = useState('');

  useEffect(() => {
    const load = async () => {
      const [gamesResponse, wishlistResponse, userResponse] = await Promise.all([
        fetch(apiUrl('/data/favorite/favorite_games'), { headers: authHeaders() }),
        fetch(apiUrl('/data/favorite'), { headers: authHeaders() }),
        fetch(apiUrl('/data/user_data'), { headers: authHeaders() }),
      ]);
      const loadedGames = await readJson<Game[]>(gamesResponse);
      if (gamesResponse.ok && Array.isArray(loadedGames)) {
        setGames(loadedGames);
        setAllGames(loadedGames);
      }
      const loadedWishlist = await readJson<string[]>(wishlistResponse);
      if (wishlistResponse.ok && Array.isArray(loadedWishlist)) setWishlist(loadedWishlist);
      const user = await readJson<{ message?: string }>(userResponse);
      if (userResponse.ok && user?.message) setUsername(user.message);
    };
    void load();
  }, []);

  const handleRemoveFromWishlist = async (gameId: string) => {
    const response = await fetch(apiUrl(`/data/favorite/remove/${gameId}`), {
      method: 'DELETE',
      headers: authHeaders(),
    });
    if (response.ok) {
      setWishlist((current) => current.filter((id) => id !== gameId));
      setGames((current) => current.filter((game) => game.appId !== gameId));
      setAllGames((current) => current.filter((game) => game.appId !== gameId));
    }
  };

  const handleSearch = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    const normalizedSearch = searchTerm.trim().toLocaleLowerCase();
    setGames(
      normalizedSearch
        ? allGames.filter((game) => game.title.toLocaleLowerCase().includes(normalizedSearch))
        : allGames,
    );
  };

  return (
    <div className="min-h-screen bg-gray-900">
      <header className="fixed top-0 z-20 flex w-full items-center justify-between bg-gray-950 p-4 text-white">
        <button className="flex items-center" onClick={() => router.push('/home')} type="button">
          <img alt="Logo" className="mr-3 h-10 w-auto" src="/steam-logo.png" />
          <span className="text-xl">GameShop</span>
        </button>
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
              <button className="block w-full bg-red-500 px-4 py-2 text-left text-white hover:bg-red-600" onClick={() => { localStorage.removeItem('token'); void router.push('/login'); }} type="button">Cerrar sesión</button>
            </div>
          )}
        </div>
      </header>
      <main className="mx-auto max-w-7xl px-6 pt-20 sm:px-8">
        <h1 className="py-8 text-center text-4xl text-white">Juegos favoritos</h1>
        <ul className="mx-auto mt-10 grid grid-cols-1 gap-8 sm:grid-cols-2 lg:grid-cols-4" role="list">
          {games.map((game) => (
            <li className="rounded-lg bg-gray-800 p-6" key={game.appId}>
              <a href={game.url} rel="noreferrer" target="_blank">
                <img alt={game.title} className="aspect-[3/2] w-full rounded object-contain object-center" src={game.imgUrl} />
                <h2 className="mt-6 text-xl font-semibold text-white">{game.title}</h2>
                <p className="text-gray-300">Valoración positiva: {game.reviewSummary ?? 'No disponible'}</p>
                <div className="mt-2 flex items-center justify-between text-white">
                  <p>Precio: {game.discountedPrice ?? game.originalPrice ?? 'No disponible'}</p>
                  <button aria-label={`Quitar ${game.title} de deseados`} onClick={(event) => { event.preventDefault(); event.stopPropagation(); void handleRemoveFromWishlist(game.appId); }} type="button">
                    <img alt="" className="h-6 w-6" src="/Estrella_llena.png" />
                  </button>
                </div>
              </a>
            </li>
          ))}
        </ul>
        {wishlist.length === 0 && <p className="py-10 text-center text-gray-300">Todavía no hay juegos en tu lista.</p>}
      </main>
    </div>
  );
};

export default Favorites;
