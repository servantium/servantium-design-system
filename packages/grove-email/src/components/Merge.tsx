/**
 * Merge — writes `{{ name }}` into the output untouched, for the sender to fill. For TSX only: in
 * an MDX master you just type {{ name }} and the loader protects it.
 */
export function Merge({ name }: { name: string }) {
  return <>{`{{ ${name} }}`}</>;
}
