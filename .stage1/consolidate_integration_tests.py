from __future__ import annotations
import ast, copy, pathlib, re, collections, json, sys

ROOT=pathlib.Path(sys.argv[1]).resolve()
BASE=ROOT/'tests'/'integration'

DOMAIN_FILES={
 'quality_gates':'test_quality_gates.py',
 'privacy_diagnostics':'test_privacy_diagnostics.py',
 'build_release':'test_build_release.py',
 'localization':'test_localization.py',
 'accessibility':'test_accessibility.py',
 'player':'test_player.py',
 'settings':'test_settings_contract.py',
 'queue_history':'test_queue_history.py',
 'providers':'test_providers.py',
 'search':'test_search.py',
 'network':'test_network.py',
 'media_processing':'test_media_processing.py',
 'download_flow':'test_download_flow.py',
 'qt_ui':'test_qt_ui.py',
 'core_services':'test_core_services.py',
}
RULES=[
('quality_gates', [r'audit',r'quality_gate',r'acceptance_gate',r'historical_gate',r'historical_failure',r'historical_regression',r'candidate_manifest',r'full_parity',r'undefined_global',r'unused_import',r'exception_allowlist',r'exception_audit',r'localization_audit',r'qt_import_audit',r'gate_',r'_gate',r'parity']),
('privacy_diagnostics',[r'support_bundle',r'privacy',r'redact',r'sanitiz',r'crash_report',r'secret',r'logging_',r'log_sanit',r'configured_url',r'home_placeholder']),
('build_release',[r'pyinstaller',r'bootstrap',r'build_',r'_build',r'release_',r'_release',r'dependency',r'third_party',r'changelog',r'version_',r'runtime_stage',r'ci_',r'frozen_',r'requirement']),
('localization',[r'localiz',r'translation',r'ui_text',r'runtime_exact',r'runtime_regex',r'ukrain',r'german',r'language',r'stage_ids',r'legacy_literals',r'localized_',r'message_ids',r'terminology']),
('accessibility',[r'accessibility',r'screen_reader',r'focus',r'tab_chain',r'qfocusframe',r'context_menu',r'keyboard',r'shortcut',r'help_center',r'help_',r'_help',r'f1',r'screenreader',r'accessib']),
('player',[r'player',r'seek',r'media_key',r'volume',r'event_sound',r'clipboard',r'tray',r'multimedia']),
('settings',[r'appsettings',r'settings',r'config_',r'_config',r'onboarding',r'first_run',r'ui_scale',r'output_dir',r'appearance',r'normalize_audio',r'normalization_mode',r'profile_']),
('queue_history',[r'queue',r'history',r'backup',r'restore',r'unfinished',r'persistence',r'resume_manifest',r'library_service',r'position_store_prunes']),
('providers',[r'knigavuhe',r'poleknig',r'audioknigi',r'playerjs',r'playlist',r'narrator',r'author_',r'_author',r'metadata',r'json_ld',r'structured_book',r'provider',r'annotation',r'narration',r'bookcontroller',r'book_title',r'coauthor']),
('search',[r'search',r'query_',r'_query',r'sorting',r'availability',r'dedup',r'searchresult',r'search_result']),
('network',[r'network',r'proxy',r'socket',r'connect_',r'http',r'cloudflare',r'dns',r'range',r'segment',r'remote_size',r'bandwidth',r'content_range',r'download_single',r'download_segmented',r'source_health',r'browser_session',r'cookie']),
('media_processing',[r'ffmpeg',r'ffprobe',r'probe',r'split',r'loudnorm',r'id3',r'sidecar',r'cover',r'duration',r'media_',r'track_status',r'audio_probe',r'timeline',r'chapter',r'atomic_write']),
('download_flow',[r'download',r'book_flow',r'missing_media',r'duplicate_preflight',r'source_cleanup',r'disk_',r'full_mp3',r'redownload',r'source_target',r'expired_media',r'selected_indices',r'download_request',r'download_mode',r'download_book',r'parts_count']),
('qt_ui',[r'ui_',r'_ui',r'theme',r'layout',r'table',r'menu',r'easy_',r'advanced_',r'dialog',r'window',r'card',r'column',r'button',r'progress',r'widget',r'main_window',r'header',r'scroll',r'row_',r'drop_',r'drag_',r'workspace']),
]

def classify(name:str)->str:
    n=name.lower()
    for domain,pats in RULES:
        if any(re.search(p,n) for p in pats):
            return domain
    return 'core_services'

def bound_names(node: ast.AST)->set[str]:
    out=set()
    if isinstance(node,(ast.FunctionDef,ast.AsyncFunctionDef,ast.ClassDef)):
        out.add(node.name)
    elif isinstance(node,ast.Assign):
        for t in node.targets:
            if isinstance(t,ast.Name): out.add(t.id)
    elif isinstance(node,ast.AnnAssign) and isinstance(node.target,ast.Name):
        out.add(node.target.id)
    return out

def import_bindings(node: ast.AST):
    out=[]
    if isinstance(node,ast.Import):
        for a in node.names:
            bound=a.asname or a.name.split('.')[0]
            spec=('import',a.name,a.asname)
            out.append((bound,spec))
    elif isinstance(node,ast.ImportFrom):
        for a in node.names:
            bound=a.asname or a.name
            spec=('from',node.module or '',a.name,a.asname,node.level)
            out.append((bound,spec))
    return out

def renamed_import(node: ast.AST, mapping: dict[str,str]):
    node=copy.deepcopy(node)
    if isinstance(node,ast.Import):
        for a in node.names:
            bound=a.asname or a.name.split('.')[0]
            if bound in mapping:
                a.asname=mapping[bound]
    elif isinstance(node,ast.ImportFrom):
        for a in node.names:
            bound=a.asname or a.name
            if bound in mapping:
                a.asname=mapping[bound]
    return node

def slug(path:pathlib.Path)->str:
    s=path.stem
    s=re.sub(r'^test_','',s)
    s=re.sub(r'[^0-9A-Za-z]+','_',s).strip('_')
    return s[-48:] or 'legacy'

class _LocalBindingCollector(ast.NodeVisitor):
    def __init__(self):
        self.bound=set()
        self.globals=set()
    def visit_Name(self,node):
        if isinstance(node.ctx,(ast.Store,ast.Del)):
            self.bound.add(node.id)
    def visit_arg(self,node):
        self.bound.add(node.arg)
    def visit_Global(self,node):
        self.globals.update(node.names)
    def visit_Import(self,node):
        for a in node.names:
            self.bound.add(a.asname or a.name.split('.')[0])
    def visit_ImportFrom(self,node):
        for a in node.names:
            self.bound.add(a.asname or a.name)
    def visit_FunctionDef(self,node):
        self.bound.add(node.name)
    def visit_AsyncFunctionDef(self,node):
        self.bound.add(node.name)
    def visit_ClassDef(self,node):
        self.bound.add(node.name)
    def visit_Lambda(self,node):
        pass

def _function_local_bindings(node):
    c=_LocalBindingCollector()
    for arg in list(node.args.posonlyargs)+list(node.args.args)+list(node.args.kwonlyargs):
        c.bound.add(arg.arg)
    if node.args.vararg: c.bound.add(node.args.vararg.arg)
    if node.args.kwarg: c.bound.add(node.args.kwarg.arg)
    for stmt in node.body:
        if isinstance(stmt,(ast.FunctionDef,ast.AsyncFunctionDef,ast.ClassDef)):
            c.bound.add(stmt.name)
        else:
            c.visit(stmt)
    return c.bound, c.globals

class Renamer(ast.NodeTransformer):
    def __init__(self,mapping):
        self.mapping=mapping
        self.blocked_stack=[set()]
    @property
    def blocked(self):
        out=set()
        for item in self.blocked_stack: out.update(item)
        return out
    def visit_Name(self,node):
        if node.id in self.mapping and node.id not in self.blocked:
            node.id=self.mapping[node.id]
        return node
    def visit_Global(self,node):
        node.names=[self.mapping.get(x,x) for x in node.names]
        return node
    def visit_Nonlocal(self,node):
        return node
    def _visit_function(self,node):
        original_name=node.name
        if original_name in self.mapping and original_name not in self.blocked:
            node.name=self.mapping[original_name]
        bound, globals_declared=_function_local_bindings(node)
        blocked=(bound - globals_declared)
        self.blocked_stack.append(blocked)
        node.decorator_list=[self.visit(x) for x in node.decorator_list]
        node.returns=self.visit(node.returns) if node.returns else None
        node.args.defaults=[self.visit(x) for x in node.args.defaults]
        node.args.kw_defaults=[self.visit(x) if x else None for x in node.args.kw_defaults]
        node.body=[self.visit(x) for x in node.body]
        self.blocked_stack.pop()
        return node
    def visit_FunctionDef(self,node): return self._visit_function(node)
    def visit_AsyncFunctionDef(self,node): return self._visit_function(node)
    def visit_ClassDef(self,node):
        original_name=node.name
        if original_name in self.mapping and original_name not in self.blocked:
            node.name=self.mapping[original_name]
        bound=set()
        for stmt in node.body:
            bound.update(bound_names(stmt))
        self.blocked_stack.append(bound)
        node.decorator_list=[self.visit(x) for x in node.decorator_list]
        node.bases=[self.visit(x) for x in node.bases]
        node.keywords=[self.visit(x) for x in node.keywords]
        node.body=[self.visit(x) for x in node.body]
        self.blocked_stack.pop()
        return node

sources=[]
for p in sorted(BASE.glob('test_*.py')):
    src=p.read_text(encoding='utf-8')
    tree=ast.parse(src, filename=str(p))
    tests=[]
    for node in tree.body:
        if isinstance(node,(ast.FunctionDef,ast.AsyncFunctionDef)) and node.name.startswith('test_'):
            tests.append((node,classify(node.name)))
    sources.append((p,src,tree,tests))

participants=collections.defaultdict(list)
for p,src,tree,tests in sources:
    doms=sorted({d for _,d in tests})
    for d in doms: participants[d].append((p,tree,tests))

manifest={"legacy_files":len(sources),"legacy_test_functions":sum(len(t) for *_,t in sources),"domains":{}}

for p,_,_,_ in sources:
    p.unlink()

for domain,filename in DOMAIN_FILES.items():
    parts=participants.get(domain,[])
    name_sources=collections.defaultdict(set)
    selected_test_names=collections.defaultdict(list)
    import_specs=collections.defaultdict(set)
    for p,tree,tests in parts:
        if not any(d==domain for _,d in tests): continue
        for node in tree.body:
            if isinstance(node,(ast.Import,ast.ImportFrom)):
                if isinstance(node,ast.ImportFrom) and node.module=='__future__':
                    continue
                for bound,spec in import_bindings(node):
                    import_specs[bound].add(spec)
                continue
            if isinstance(node,(ast.FunctionDef,ast.AsyncFunctionDef)) and node.name.startswith('test_'):
                if classify(node.name)==domain:
                    selected_test_names[node.name].append(p)
                continue
            for name in bound_names(node):
                if name != 'ROOT': name_sources[name].add(p)
    collisions={name for name,ps in name_sources.items() if len(ps)>1}
    import_collisions={name for name,specs in import_specs.items() if len(specs)>1}
    test_collisions={name for name,ps in selected_test_names.items() if len(ps)>1}

    future_imports=set(); imports=[]; import_seen=set(); sections=[]; domain_tests=[]
    for p,tree,tests in parts:
        chosen=[n for n,d in tests if d==domain]
        if not chosen: continue
        suffix=slug(p)
        rename={name:f'{name}__{suffix}' for name in collisions}
        rename.update({name:f'{name}__{suffix}' for name in import_collisions})
        for name in test_collisions:
            if any(n.name==name for n in chosen): rename[name]=f'{name}__{suffix}'

        section_nodes=[]
        for node in tree.body:
            if isinstance(node,ast.ImportFrom) and node.module=='__future__':
                future_imports.add(ast.unparse(node)); continue
            if isinstance(node,(ast.Import,ast.ImportFrom)):
                imp=renamed_import(node,rename)
                text=ast.unparse(imp)
                if text not in import_seen:
                    import_seen.add(text); imports.append(text)
                continue
            if isinstance(node,(ast.FunctionDef,ast.AsyncFunctionDef)) and node.name.startswith('test_'):
                if classify(node.name)!=domain: continue
            elif isinstance(node,ast.Expr) and isinstance(node.value,(ast.Constant,)) and isinstance(node.value.value,str):
                continue
            new=copy.deepcopy(node)
            if rename:
                new=Renamer(rename).visit(new)
                ast.fix_missing_locations(new)
            section_nodes.append(new)
        code='\n\n'.join(ast.unparse(n) for n in section_nodes).strip()
        if code:
            sections.append(f'# Origin: {p.name}\n{code}')
        for n in chosen:
            domain_tests.append(rename.get(n.name,n.name))

    out=[]
    out.append('"""Consolidated integration tests for the %s domain.\n\nHistorical origin is recorded above each migrated section; detailed round history remains in audits/ and Git.\n"""' % domain.replace('_',' '))
    if future_imports:
        out.extend(sorted(future_imports))
    if imports:
        out.append('\n'.join(imports))
    out.extend(sections)
    target=BASE/filename
    target.write_text('\n\n\n'.join(out).rstrip()+'\n',encoding='utf-8')
    manifest['domains'][filename]={"tests":len(domain_tests),"source_files":len(parts),"test_names":domain_tests}

lines=[
'# Integration test consolidation map',
'',
'The historical round-oriented integration modules were consolidated by behavior domain.',
'Round/audit history remains in `audits/4.12/rounds/` and Git history.',
'',
'## Domain files',
''
]
for fn,data in manifest['domains'].items():
    lines.append(f'- `{fn}` — {data["tests"]} tests, sourced from {data["source_files"]} historical modules.')
lines += ['', '## Historical file mapping', '']
for p,src,tree,tests in sources:
    by=collections.Counter(classify(n.name) for n,_d in tests)
    targets=', '.join(f'`{DOMAIN_FILES[d]}` ({count})' for d,count in sorted(by.items()))
    lines.append(f'- `{p.name}` → {targets}')
(BASE/'README.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
(BASE/'consolidation_manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps({"legacy_files":manifest['legacy_files'],"tests":manifest['legacy_test_functions'],"new_modules":len(DOMAIN_FILES),"counts":{k:v['tests'] for k,v in manifest['domains'].items()}},ensure_ascii=False,indent=2))
