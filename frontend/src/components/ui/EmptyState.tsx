export function EmptyState({
  title,
  description,
  action,
}: {
  title: string;
  description?: string;
  action?: React.ReactNode;
}) {
  return (
    <div className="flex flex-col items-center justify-center py-20 text-center">
      <p className="mb-2 text-lg font-semibold text-navy">{title}</p>
      {description ? <p className="mb-6 text-mist max-w-xs">{description}</p> : null}
      {action ? <div>{action}</div> : null}
    </div>
  );
}
