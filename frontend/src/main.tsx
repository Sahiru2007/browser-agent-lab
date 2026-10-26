import { StrictMode, useEffect, useState } from 'react';
import { createRoot } from 'react-dom/client';
import type { FormEvent } from 'react';
import './style.css';

type Customer = {id: number; name: string; email: string; company: string};

function App() {
  const [customers, setCustomers] = useState<Customer[]>([]);
  const [query, setQuery] = useState('');
  const [message, setMessage] = useState('');
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    const controller = new AbortController();
    fetch('/api/customers?q=' + encodeURIComponent(query), {signal: controller.signal})
      .then(response => {if (!response.ok) throw new Error(); return response.json();})
      .then(data => {setCustomers(data); setError('');})
      .catch(err => {if (err.name !== 'AbortError') setError('Customer list could not be loaded.');});
    return () => controller.abort();
  }, [query]);

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const form = event.currentTarget;
    const payload = Object.fromEntries(new FormData(form));
    setBusy(true); setMessage('');
    const controller = new AbortController();
    const timer = window.setTimeout(() => controller.abort(), 700);
    try {
      const response = await fetch('/api/customers', {
        method: 'POST', headers: {'Content-Type': 'application/json'},
        body: JSON.stringify(payload), signal: controller.signal,
      });
      if (!response.ok) throw new Error('Server rejected the request.');
      await response.json();
      setMessage('Customer saved.');
      form.reset();
      // Refresh explicitly; changing an already-empty query would not rerun useEffect.
      setQuery('');
      const refreshed = await fetch('/api/customers');
      if (!refreshed.ok) throw new Error('List refresh failed after save.');
      setCustomers(await refreshed.json());
    } catch {
      setMessage('Could not confirm whether the customer was saved.');
    } finally {
      window.clearTimeout(timer); setBusy(false);
    }
  }

  return <div className="shell">
    <aside><a className="brand" href="/">fieldwork<span>CRM</span></a><p className="workspace">DEMONSTRATION WORKSPACE</p><div className="nav-active">Customers <span>↗</span></div><p className="aside-note">Synthetic customer records.<br />Local evaluation environment.</p></aside>
    <main>
      <header><div><p className="eyebrow">WORKSPACE / CUSTOMERS</p><h1>Customer directory</h1><p className="subtitle">Find a customer or add someone new.</p></div><span className="badge">Local demo</span></header>
      <div className="columns">
        <section className="panel directory"><div className="panel-heading"><h2>Customers</h2><span className="count">{customers.length} shown</span></div>
          <label htmlFor="search">Search by name or email</label>
          <input id="search" value={query} onChange={e => setQuery(e.target.value)} placeholder="Search customers…" />
          {error && <p role="alert">{error}</p>}
          <div className="table-wrap"><table><thead><tr><th>Customer</th><th>Company</th></tr></thead><tbody>{customers.map(c => <tr key={c.id}><td><strong>{c.name}</strong><span className="email">{c.email}</span></td><td>{c.company}</td></tr>)}</tbody></table></div>
          {!customers.length && !error && <p className="empty">No matching customers.</p>}
        </section>
        <section className="panel"><div className="panel-heading"><h2>Add customer</h2><span className="step">01</span></div><p className="form-note">Enter the customer's contact details.</p>
          <form onSubmit={submit}>
            <label htmlFor="name">Full name</label><input id="name" name="name" required maxLength={120} placeholder="e.g. Nimal Silva" />
            <label htmlFor="email">Email address</label><input id="email" name="email" type="email" required maxLength={254} placeholder="name@example.test" />
            <label htmlFor="company">Company</label><input id="company" name="company" required maxLength={120} placeholder="Company name" />
            <button disabled={busy} type="submit">{busy ? 'Saving…' : 'Save customer'}</button>
            <p role="status" aria-live="polite" className="status">{message}</p>
          </form>
        </section>
      </div>
      <footer>Fieldwork CRM · Browser Agent Lab · Milestone 01</footer>
    </main>
  </div>;
}

createRoot(document.getElementById('root')!).render(<StrictMode><App /></StrictMode>);
