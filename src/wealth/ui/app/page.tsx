import Link from "next/link";

export default function Home() {
  return (
    <div className="p-8">
      <h1 className="text-2xl font-bold mb-4">Wealth Dashboard</h1>
      <div className="space-x-4">
        <Link className="underline" href="/accounts">Accounts</Link>
        <Link className="underline" href="/transactions">Transactions</Link>
      </div>
      <p className="mt-6 text-muted-foreground">Use the links above to manage your portfolio.</p>
    </div>
  );
}
