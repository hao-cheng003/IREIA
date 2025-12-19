import Link from "next/link";

export default function Home() {
  return (
    <main className="container">
      <div className="card">
        <h1>IREA</h1>
        <p>Boston Real Estate – Demo</p>
        <p>
          <Link href="/predict">Go to Predict →</Link>
        </p>
      </div>
    </main>
  );
}
