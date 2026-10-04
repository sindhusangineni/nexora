import { AppProviders } from "./providers/AppProviders";
import { AppRouter } from "./router/AppRouter";
import { OfflineBanner, PwaInstallBanner } from "@/shared/pwa";

function App() {
    return (
        <AppProviders>
            <OfflineBanner />
            <AppRouter />
            <PwaInstallBanner />
        </AppProviders>
    );
}

export default App;
