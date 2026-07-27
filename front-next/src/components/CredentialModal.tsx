import React, { RefObject, useEffect, useRef } from 'react';


export interface CredentialModalProps {
  open: boolean;
  title: string;
  description: string;
  missingCredentials?: string[];
  onClose: () => void;
  returnFocusRef?: RefObject<HTMLElement>;
}


const CredentialModal = ({
  open,
  title,
  description,
  missingCredentials = [],
  onClose,
  returnFocusRef,
}: CredentialModalProps) => {
  const closeButtonRef = useRef<HTMLButtonElement>(null);

  useEffect(() => {
    if (!open) return;

    const previousFocus = document.activeElement as HTMLElement | null;
    const requestedReturnFocus = returnFocusRef?.current;
    closeButtonRef.current?.focus();
    const handleKeyDown = (event: KeyboardEvent) => {
      if (event.key === 'Escape') onClose();
    };
    document.addEventListener('keydown', handleKeyDown);

    return () => {
      document.removeEventListener('keydown', handleKeyDown);
      (requestedReturnFocus ?? previousFocus)?.focus?.();
    };
  }, [onClose, open, returnFocusRef]);

  if (!open) return null;

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/75 p-4"
      data-testid="credential-modal-backdrop"
      onMouseDown={(event) => {
        if (event.target === event.currentTarget) onClose();
      }}
    >
      <section
        aria-describedby="credential-modal-description"
        aria-labelledby="credential-modal-title"
        aria-modal="true"
        className="w-full max-w-lg rounded-xl border border-slate-600 bg-slate-900 p-7 text-white shadow-2xl"
        role="dialog"
      >
        <h2 className="text-2xl font-semibold" id="credential-modal-title">
          {title}
        </h2>
        <p className="mt-4 leading-7 text-slate-300" id="credential-modal-description">
          {description}
        </p>
        {missingCredentials.length > 0 && (
          <div className="mt-5 rounded-lg bg-slate-800 p-4">
            <p className="text-sm text-slate-300">Variables necesarias:</p>
            <ul className="mt-2 space-y-1 font-mono text-sm text-amber-300">
              {missingCredentials.map((credential) => (
                <li key={credential}>{credential}</li>
              ))}
            </ul>
          </div>
        )}
        <button
          className="mt-6 w-full rounded-lg bg-blue-600 px-4 py-2 font-medium hover:bg-blue-500 focus:outline-none focus:ring-2 focus:ring-blue-300"
          onClick={onClose}
          ref={closeButtonRef}
          type="button"
        >
          Entendido
        </button>
      </section>
    </div>
  );
};

export default CredentialModal;
