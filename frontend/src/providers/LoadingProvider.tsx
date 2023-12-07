import { createContext, useContext, useState } from "react";

const loadingContext = createContext(false);
const setLoadingContext = createContext(
  null as ((loading: boolean) => void) | null
);

export default function LoadingProvider({
  children,
}: {
  children: React.ReactNode;
}) {
  const [loading, setLoading] = useState(false);

  return (
    <loadingContext.Provider value={loading}>
      <setLoadingContext.Provider value={setLoading}>
        {children}
      </setLoadingContext.Provider>
    </loadingContext.Provider>
  );
}

export function useLoading(): [boolean, (loading: boolean) => void] {
    const loading = useContext(loadingContext);
    const setLoading = useContext(setLoadingContext);

    return [loading, setLoading as (loading: boolean) => void];
}
