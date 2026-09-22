import { readFileSync, readdirSync } from 'node:fs'
import { resolve } from 'node:path'
import { parse } from '@vue/compiler-sfc'

const root = resolve(import.meta.dirname, '..')
function vueFiles(directory) {
  return readdirSync(directory, { withFileTypes: true }).flatMap((entry) => {
    const path = resolve(directory, entry.name)
    if (entry.isDirectory()) return vueFiles(path)
    return entry.name.endsWith('.vue') ? [path] : []
  })
}
const files = ['components', 'layouts', 'pages'].flatMap((directory) => vueFiles(resolve(root, directory)))
let failed = false
for (const file of files) {
  const source = readFileSync(file, 'utf8')
  const result = parse(source, { filename: file })
  if (result.errors.length) {
    failed = true
    console.error(`${file}:`, result.errors)
  }
}
if (failed) process.exit(1)
console.log(`Parsed ${files.length} Vue files.`)
