function urlBase64ToUint8Array(base64String) {
    const padding = '='.repeat((4 - (base64String.length % 4)) % 4);
    const base64 = (base64String + padding).replace(/-/g, '+').replace(/_/g, '/');
    const rawData = atob(base64);
    const outputArray = new Uint8Array(rawData.length);
    for (let i = 0; i < rawData.length; ++i) {
        outputArray[i] = rawData.charCodeAt(i);
    }
    return outputArray;
}

async function subscribeToPush() {
    if (!window.VAPID_PUBLIC_KEY) {
        alert('Las notificaciones push no están configuradas todavía.');
        return false;
    }

    if (!('serviceWorker' in navigator) || !('PushManager' in window)) {
        alert('Tu navegador no soporta notificaciones push.');
        return false;
    }

    const permission = await Notification.requestPermission();
    if (permission !== 'granted') {
        alert('Necesitamos permiso para enviarte notificaciones.');
        return false;
    }

    const registration = await navigator.serviceWorker.ready;
    let subscription = await registration.pushManager.getSubscription();

    if (!subscription) {
        subscription = await registration.pushManager.subscribe({
            userVisibleOnly: true,
            applicationServerKey: urlBase64ToUint8Array(window.VAPID_PUBLIC_KEY),
        });
    }

    const response = await fetch('/api/push/subscribe', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(subscription.toJSON()),
    });

    if (response.ok) {
        document.querySelectorAll('#push-prompt, #global-push-prompt').forEach((el) => {
            if (el) {
                el.innerHTML = '<p>✅ Notificaciones activadas. Vas a recibir avisos del gym.</p>';
                el.style.display = 'block';
            }
        });
        return true;
    }

    return false;
}

document.addEventListener('DOMContentLoaded', () => {
    document.querySelectorAll('#enable-push-btn, #global-enable-push-btn').forEach((btn) => {
        btn.addEventListener('click', subscribeToPush);
    });

    if (!window.VAPID_PUBLIC_KEY) return;

    if (Notification.permission === 'granted') {
        subscribeToPush();
        const banner = document.getElementById('global-push-prompt');
        if (banner) banner.style.display = 'none';
        return;
    }

    if (Notification.permission === 'denied') {
        const banner = document.getElementById('global-push-prompt');
        if (banner) {
            banner.innerHTML = '<p>⚠️ Tenés las notificaciones bloqueadas. Activálas en ajustes del navegador/celular.</p>';
        }
    }
});
