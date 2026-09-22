import { readdir, readFile } from 'node:fs/promises'
import { extname, join, relative, sep } from 'node:path'
import { compileTemplate, parse } from '@vue/compiler-sfc'

const root = new URL('..', import.meta.url).pathname
const ignoredSegments = new Set(['.nuxt', '.output', 'node_modules', 'components/ui'])
const forbidden = /<(button|input|select|textarea|table|thead|tbody|tr|th|td)(?=[\s>])/g
const legacyClasses = /\b(primary-button|quiet-button|brand-button|field-control)\b/g
const findings = []

async function visit(directory) {
  for (const entry of await readdir(directory, { withFileTypes: true })) {
    const path = join(directory, entry.name)
    const relativePath = relative(root, path).split(sep).join('/')
    if (entry.isDirectory()) {
      if (![...ignoredSegments].some((segment) => relativePath === segment || relativePath.startsWith(`${segment}/`))) await visit(path)
      continue
    }
    if (extname(entry.name) !== '.vue') continue
    const source = await readFile(path, 'utf8')
    const parsed = parse(source, { filename: relativePath })
    for (const error of parsed.errors) findings.push(`${relativePath}: ${error.message || error}`)
    if (parsed.descriptor.template) {
      const compiled = compileTemplate({
        id: relativePath,
        filename: relativePath,
        source: parsed.descriptor.template.content,
      })
      for (const error of compiled.errors) findings.push(`${relativePath}: ${error.message || error}`)
    }
    for (const match of source.matchAll(forbidden)) {
      const line = source.slice(0, match.index).split('\n').length
      findings.push(`${relativePath}:${line} raw <${match[1]}>; use the matching component from components/ui`)
    }
    for (const match of source.matchAll(legacyClasses)) {
      const line = source.slice(0, match.index).split('\n').length
      findings.push(`${relativePath}:${line} legacy ${match[1]} class; use a components/ui variant instead`)
    }
  }
}

await visit(root)

if (findings.length) {
  console.error(findings.join('\n'))
  console.error(`\n${findings.length} UI boundary finding(s) found.`)
  process.exit(1)
}

console.log('Shadcn UI boundary is clean.')
