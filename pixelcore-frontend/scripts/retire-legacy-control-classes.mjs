import { readdir, readFile, writeFile } from 'node:fs/promises'
import { extname, join, relative, sep } from 'node:path'

const root = new URL('..', import.meta.url).pathname
const ignoredSegments = ['.nuxt', '.output', 'node_modules', 'components/ui']
let changedFiles = 0

function cleanClassAttribute(tag) {
  return tag.replace(/\sclass="([^"]*)"/, (_, value) => {
    const classes = value.split(/\s+/).filter(Boolean).filter((name) => !['primary-button', 'quiet-button', 'brand-button', 'field-control'].includes(name))
    return classes.length ? ` class="${classes.join(' ')}"` : ''
  })
}

function migrateButtonLinks(source) {
  return source.replace(/<NuxtLink\b([^>]*\bclass="[^"]*(?:primary-button|quiet-button|brand-button)[^"]*"[^>]*)>([\s\S]*?)<\/NuxtLink>/g, (_, attributes, content) => {
    const variant = /\bquiet-button\b/.test(attributes) ? ' variant="outline"' : ''
    return `<ButtonLink${variant}${cleanClassAttribute(` ${attributes}`).trimEnd()}>${content}</ButtonLink>`
  })
}

function migrateComponents(source) {
  return source.replace(/<(Button|Input|Textarea|NativeSelect)\b[^>]*>/g, (tag) => cleanClassAttribute(tag))
}

async function visit(directory) {
  for (const entry of await readdir(directory, { withFileTypes: true })) {
    const path = join(directory, entry.name)
    const relativePath = relative(root, path).split(sep).join('/')
    if (entry.isDirectory()) {
      if (!ignoredSegments.some((segment) => relativePath === segment || relativePath.startsWith(`${segment}/`))) await visit(path)
      continue
    }
    if (extname(entry.name) !== '.vue') continue
    const source = await readFile(path, 'utf8')
    const migrated = migrateComponents(migrateButtonLinks(source))
    if (migrated === source) continue
    await writeFile(path, migrated)
    changedFiles += 1
  }
}

await visit(root)
console.log(`Retired legacy control classes in ${changedFiles} Vue files.`)
