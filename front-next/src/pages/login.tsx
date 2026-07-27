import React, { FormEvent, useCallback, useState } from 'react';
import { useRouter } from 'next/router';

import CredentialModal from '@/components/CredentialModal';
import { apiUrl, readJson } from '@/lib/api';
import type { IntegrationStatus } from '@/types/game';


interface LoginResponse {
  token?: string;
  message?: string;
}

interface GoogleLoginResponse extends Partial<IntegrationStatus> {
  link?: string;
  message?: string;
}


const Login = () => {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [googleStatus, setGoogleStatus] = useState<IntegrationStatus | null>(null);
  const router = useRouter();

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setError('');
    try {
      const response = await fetch(apiUrl('/login/user/login'), {
        method: 'POST',
        headers: { Accept: 'application/json', 'Content-Type': 'application/json' },
        body: JSON.stringify({ contrasenia: password, correo: email }),
      });
      const content = await readJson<LoginResponse>(response);
      if (response.ok && content?.token) {
        localStorage.setItem('token', content.token);
        await router.push('/home');
        return;
      }
      setError(content?.message ?? 'El usuario o la contraseña no son correctos.');
    } catch {
      setError('No se ha podido conectar con el servicio de inicio de sesión.');
    }
  };

  const handleGoogleLogin = async () => {
    setError('');
    try {
      const response = await fetch(apiUrl('/login/user/login/google'), {
        credentials: 'include',
        headers: { Accept: 'application/json' },
      });
      const data = await readJson<GoogleLoginResponse>(response);
      if (!response.ok || !data?.link) {
        if (data?.configured === false) {
          setGoogleStatus({
            service: 'google',
            configured: false,
            missingCredentials: data.missingCredentials ?? [],
          });
        } else {
          setError(data?.message ?? 'No se ha podido iniciar la conexión con Google.');
        }
        return;
      }

      const popup = window.open(data.link, 'google-login', 'height=700,width=700');
      if (!popup) {
        setError('El navegador ha bloqueado la ventana de Google. Permite ventanas emergentes y vuelve a intentarlo.');
        return;
      }

      const finish = () => {
        window.removeEventListener('message', handleMessage);
        window.clearInterval(closeWatcher);
      };
      const handleMessage = (event: MessageEvent) => {
        if (event.origin !== window.location.origin || event.source !== popup) return;
        const accessToken = (event.data as { access_token?: unknown })?.access_token;
        if (typeof accessToken === 'string' && accessToken) {
          localStorage.setItem('token', accessToken);
          finish();
          void router.push('/home');
        }
      };
      window.addEventListener('message', handleMessage);
      const closeWatcher = window.setInterval(() => {
        if (popup.closed) finish();
      }, 500);
    } catch {
      setError('No se ha podido conectar con Google.');
    }
  };

  const closeGoogleModal = useCallback(() => setGoogleStatus(null), []);

  return (
    <div className="flex h-screen flex-col items-center justify-center bg-slate-950">
      <div className="m-4 w-full bg-slate-900 p-8 text-white shadow-xl md:w-3/4 lg:w-1/2">
        <h1 className="mb-6 text-center text-3xl">Inicio de sesión</h1>
        <form className="space-y-3" onSubmit={handleSubmit}>
          <div>
            <label className="mb-1 text-sm" htmlFor="email">Correo electrónico</label>
            <input className="w-full rounded border px-3 py-2 text-black" id="email" onChange={(event) => setEmail(event.target.value)} required type="email" value={email} />
          </div>
          <div>
            <label className="mb-1 text-sm" htmlFor="password">Contraseña</label>
            <input className="w-full rounded border px-3 py-2 text-black" id="password" onChange={(event) => setPassword(event.target.value)} required type="password" value={password} />
          </div>
          <button className="w-full rounded bg-blue-600 px-3 py-2 text-white" type="submit">Iniciar sesión</button>
        </form>
        <button className="mt-4 w-full rounded bg-red-600 px-3 py-2 text-white" onClick={handleGoogleLogin} type="button">Iniciar sesión con Google</button>
        {error && <p className="mt-4 rounded bg-red-950 p-3 text-sm text-red-200" role="alert">{error}</p>}
        <div className="mt-4 flex justify-between">
          <button className="text-blue-400" onClick={() => router.push('/register')} type="button">Registrarse</button>
        </div>
      </div>
      <CredentialModal
        description="El inicio de sesión con Google está desactivado hasta que se configuren las siguientes variables en el archivo .env y se recree el servicio de login."
        missingCredentials={googleStatus?.missingCredentials}
        onClose={closeGoogleModal}
        open={googleStatus !== null}
        title="Credenciales de Google necesarias"
      />
    </div>
  );
};

export default Login;
