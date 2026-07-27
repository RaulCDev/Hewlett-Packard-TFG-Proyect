import React, { FormEvent, useState } from 'react';
import { useRouter } from 'next/router';

import { apiUrl, readJson } from '@/lib/api';


const RegisterPage = () => {
  const [fullName, setFullName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [message, setMessage] = useState('');
  const router = useRouter();

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (password !== confirmPassword) {
      setMessage('No coinciden las contraseñas.');
      return;
    }

    try {
      const response = await fetch(apiUrl('/login/user/register'), {
        method: 'POST',
        headers: { Accept: 'application/json', 'Content-Type': 'application/json' },
        body: JSON.stringify({ nombre: fullName, correo: email, contrasenia: password }),
      });
      const content = await readJson<{ message?: string }>(response);
      setMessage(content?.message ?? 'No se ha podido completar el registro.');
      if (response.ok && content?.message === 'Deberia estar guardado') {
        window.setTimeout(() => void router.push('/login'), 800);
      }
    } catch {
      setMessage('No se ha podido conectar con el servicio de registro.');
    }
  };

  return (
    <div className="flex h-screen flex-col items-center justify-center bg-slate-950">
      <div className="m-4 w-full bg-slate-900 p-8 text-white shadow-xl md:w-3/4 lg:w-1/2">
        <h1 className="mb-6 text-center text-3xl">Registrarse</h1>
        <form className="space-y-3" onSubmit={handleSubmit}>
          <div>
            <label className="mb-1 text-sm" htmlFor="fullName">Nombre completo</label>
            <input className="w-full rounded border px-3 py-2 text-black" id="fullName" onChange={(event) => setFullName(event.target.value)} required type="text" value={fullName} />
          </div>
          <div>
            <label className="mb-1 text-sm" htmlFor="email">Correo electrónico</label>
            <input className="w-full rounded border px-3 py-2 text-black" id="email" onChange={(event) => setEmail(event.target.value)} required type="email" value={email} />
          </div>
          <div>
            <label className="mb-1 text-sm" htmlFor="password">Contraseña</label>
            <input className="w-full rounded border px-3 py-2 text-black" id="password" onChange={(event) => setPassword(event.target.value)} required type="password" value={password} />
          </div>
          <div>
            <label className="mb-1 text-sm" htmlFor="confirmPassword">Confirmar contraseña</label>
            <input className="w-full rounded border px-3 py-2 text-black" id="confirmPassword" onChange={(event) => setConfirmPassword(event.target.value)} required type="password" value={confirmPassword} />
          </div>
          <button className="w-full rounded bg-blue-600 px-3 py-2 text-white" type="submit">Registrarse</button>
        </form>
        {message && <p className="mt-4 rounded bg-slate-800 p-3" role="status">{message}</p>}
        <button className="mt-4 text-blue-400" onClick={() => router.push('/login')} type="button">Volver al inicio de sesión</button>
      </div>
    </div>
  );
};

export default RegisterPage;
