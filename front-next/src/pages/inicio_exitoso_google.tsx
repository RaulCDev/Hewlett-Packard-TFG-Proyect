import { useEffect } from 'react';
//Esta pagina se utiliza para redireccionar a la siguiente y guardar correctamente el token de google
const SuccessfulGoogleLogin = () => {
    useEffect(() => {
        // Extrae el token de acceso de la URL
        const urlParams = new URLSearchParams(window.location.search);
        const token = urlParams.get('access_token');

        // Envía el token a la ventana principal
        if (window.opener && token) {
            window.opener.postMessage({ access_token: token }, window.location.origin);
        }

        // Cierra la ventana emergente
        window.close();
    }, []);

    return null;  // Este componente no necesita renderizar nada
};

export default SuccessfulGoogleLogin;
