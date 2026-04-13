import { useState } from 'react';

export function useConfirmModal() {
  const [isOpen, setIsOpen] = useState(false);
  const [message, setMessage] = useState('');
  const [resolveFunc, setResolveFunc] = useState(null);

  const confirm = (msg) => {
    return new Promise((resolve) => {
      setMessage(msg);
      setResolveFunc(() => resolve);
      setIsOpen(true);
    });
  };

  const handleConfirm = () => {
    setIsOpen(false);
    resolveFunc?.(true);
  };

  const handleCancel = () => {
    setIsOpen(false);
    resolveFunc?.(false);
  };

  const Modal = () => {
    if (!isOpen) return null;

    return (
      <div
        style={{
          position: 'fixed',
          top: 0,
          left: 0,
          right: 0,
          bottom: 0,
          backgroundColor: 'rgba(0, 0, 0, 0.5)',
          display: 'flex',
          justifyContent: 'center',
          alignItems: 'center',
          zIndex: 1000,
        }}
        onClick={handleCancel}
      >
        <div
          style={{
            backgroundColor: '#fff',
            borderRadius: 10,
            padding: 24,
            maxWidth: 400,
            boxShadow: '0 4px 16px rgba(0, 0, 0, 0.2)',
          }}
          onClick={(e) => e.stopPropagation()}
        >
          <p
            style={{
              margin: '0 0 20px 0',
              fontSize: 14,
              lineHeight: 1.5,
              color: '#333',
            }}
          >
            {message}
          </p>
          <div
            style={{
              display: 'flex',
              gap: 12,
              justifyContent: 'flex-end',
            }}
          >
            <button
              type="button"
              onClick={handleCancel}
              style={{
                padding: '8px 16px',
                borderRadius: 6,
                border: '1px solid #ccc',
                backgroundColor: '#f1f1f1',
                cursor: 'pointer',
                fontSize: 14,
                fontWeight: 500,
              }}
            >
              Cancel
            </button>
            <button
              type="button"
              onClick={handleConfirm}
              style={{
                padding: '8px 16px',
                borderRadius: 6,
                border: '1px solid #a83232',
                backgroundColor: '#a83232',
                color: '#fff',
                cursor: 'pointer',
                fontSize: 14,
                fontWeight: 600,
              }}
            >
              Confirm
            </button>
          </div>
        </div>
      </div>
    );
  };

  return { confirm, Modal };
}
