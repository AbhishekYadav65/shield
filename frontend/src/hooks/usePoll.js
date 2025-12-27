import { useEffect, useState } from "react";

export default function usePoll(fetchFn, interval = 3000) {
  const [data, setData] = useState(null);

  useEffect(() => {
    let active = true;

    async function poll() {
      const result = await fetchFn();
      if (active) setData(result);
    }

    poll();
    const id = setInterval(poll, interval);

    return () => {
      active = false;
      clearInterval(id);
    };
  }, [fetchFn, interval]);

  return data;
}
