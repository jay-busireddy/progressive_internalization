import json, random, urllib.request, urllib.error

class ChatModel:
    def __init__(self, backend="mock", model="mock", base_url=None, temperature=0.2, seed=0, max_tokens=320, timeout=300, num_ctx=None):
        self.backend = backend
        self.model = model
        self.base_url = base_url
        self.temperature = temperature
        self.seed = seed
        self.max_tokens = max_tokens
        self.timeout = timeout
        self.num_ctx = num_ctx
        self.last_usage = {"prompt_tokens":0,"completion_tokens":0}
        self.total_usage = {"prompt_tokens":0,"completion_tokens":0,"calls":0}
        random.seed(seed)

    def reset_usage(self):
        self.last_usage = {"prompt_tokens":0,"completion_tokens":0}
        self.total_usage = {"prompt_tokens":0,"completion_tokens":0,"calls":0}

    def usage(self):
        return dict(self.total_usage)

    def _record_usage(self, prompt_tokens=0, completion_tokens=0):
        self.last_usage={"prompt_tokens":int(prompt_tokens or 0),"completion_tokens":int(completion_tokens or 0)}
        self.total_usage["prompt_tokens"] += self.last_usage["prompt_tokens"]
        self.total_usage["completion_tokens"] += self.last_usage["completion_tokens"]
        self.total_usage["calls"] += 1

    def chat(self, system, user, max_tokens=None):
        limit = int(max_tokens or self.max_tokens)
        if self.backend == "mock":
            self._record_usage(max(1,(len(system)+len(user))//4), 20)
            return self._mock(user)
        if self.backend == "ollama":
            return self._ollama(system, user, limit)
        if self.backend == "openai_compat":
            return self._openai_compat(system, user, limit)
        raise ValueError(f"Unknown backend: {self.backend}")

    def _ollama(self, system, user, max_tokens):
        url = (self.base_url or "http://127.0.0.1:11434") + "/api/chat"
        options={"temperature": self.temperature, "seed": self.seed, "num_predict": max_tokens}
        if self.num_ctx:
            options["num_ctx"] = int(self.num_ctx)
        payload = {
            "model": self.model,
            "messages": [{"role":"system","content":system},{"role":"user","content":user}],
            "stream": False,
            "options": options
        }
        req = urllib.request.Request(url, data=json.dumps(payload).encode(), headers={"Content-Type":"application/json"})
        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as r:
                data = json.loads(r.read().decode())
            self._record_usage(data.get("prompt_eval_count",0),data.get("eval_count",0))
            return data["message"]["content"]
        except urllib.error.URLError as e:
            raise RuntimeError(f"Could not reach Ollama at {url}: {e}")

    def _openai_compat(self, system, user, max_tokens):
        url = (self.base_url or "http://127.0.0.1:8080/v1").rstrip("/") + "/chat/completions"
        payload = {
            "model": self.model,
            "messages": [{"role":"system","content":system},{"role":"user","content":user}],
            "temperature": self.temperature,
            "max_tokens": max_tokens,
            "seed": self.seed
        }
        req = urllib.request.Request(url, data=json.dumps(payload).encode(), headers={"Content-Type":"application/json"})
        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as r:
                data = json.loads(r.read().decode())
            usage=data.get("usage",{})
            self._record_usage(usage.get("prompt_tokens",0),usage.get("completion_tokens",0))
            return data["choices"][0]["message"]["content"]
        except urllib.error.URLError as e:
            raise RuntimeError(f"Could not reach local OpenAI-compatible server at {url}: {e}")

    def _mock(self, user):
        low = user.lower()
        if '"answers"' in user and "include every question id" in low:
            import re
            ids=[]
            qblock=user.split("QUESTIONS:",1)[-1].split("Return ONLY",1)[0]
            for m in re.finditer(r"^(q\d+)\s*:",qblock,re.M):
                if m.group(1) not in ids: ids.append(m.group(1))
            return json.dumps({"answers":[{"id":qid,"answer":"unknown"} for qid in ids]})
        if "return strict json" in low or "json object" in low:
            return json.dumps({
                "observed": ["stored observation"],
                "inferred": [],
                "hypotheses": [],
                "unresolved": ["insufficient information"],
                "reactivated": [],
                "revisions": [],
                "connections": []
            })
        terms = []
        for t in ["secondary", "production", "traffic", "identity", "database", "rollback", "routing", "cache", "queue", "replica"]:
            if t in low: terms.append(t)
        return "Mock response: " + " ".join(terms)
