import React from 'react';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';

import CredentialModal from './CredentialModal';


describe('CredentialModal', () => {
  it('identifies the missing credential and closes with its button', async () => {
    const onClose = vi.fn();
    const user = userEvent.setup();

    render(
      <CredentialModal
        open
        title="Datos locales de RapidAPI en uso"
        description="Se están mostrando los datos locales porque falta la credencial."
        missingCredentials={['RAPIDAPI_KEY']}
        onClose={onClose}
      />,
    );

    expect(screen.getByRole('dialog')).toBeInTheDocument();
    expect(screen.getByText('RAPIDAPI_KEY')).toBeInTheDocument();
    await user.click(screen.getByRole('button', { name: 'Entendido' }));
    expect(onClose).toHaveBeenCalledTimes(1);
  });

  it('closes with Escape or a backdrop click, but not from the panel', async () => {
    const onClose = vi.fn();
    const user = userEvent.setup();
    render(
      <CredentialModal
        open
        title="Credenciales de Google necesarias"
        description="Configura Google OAuth."
        missingCredentials={['GOOGLE_CLIENT_ID', 'GOOGLE_CLIENT_SECRET']}
        onClose={onClose}
      />,
    );

    await user.click(screen.getByRole('dialog'));
    expect(onClose).not.toHaveBeenCalled();
    await user.keyboard('{Escape}');
    expect(onClose).toHaveBeenCalledTimes(1);

    await user.click(screen.getByTestId('credential-modal-backdrop'));
    expect(onClose).toHaveBeenCalledTimes(2);
  });
});
