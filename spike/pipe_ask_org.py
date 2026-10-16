"""
title: Ask the Org (spike)
requirements: falkordb
"""

# Spike Pipe: proves an Open WebUI Pipe can query FalkorDB and emit status, source and embeds events.

import html
from falkordb import FalkorDB
from pydantic import BaseModel, Field

DECISIONS_FOR_SYSTEM = """
MATCH (s:System {name:$name})<-[:AFFECTS]-(d:Decision)-[:DECIDED_IN]->(doc:Doc),
      (d)-[:MADE_BY]->(p:Person), (t:Team)-[:OWNS]->(s)
RETURN d.title AS decision, d.at AS at, p.name AS by, doc.title AS doc, doc.url AS url, t.name AS team
"""


class Pipe:
    class Valves(BaseModel):
        FALKORDB_HOST: str = Field(default="falkordb")
        FALKORDB_PORT: int = Field(default=6379)
        GRAPH: str = Field(default="org:spike")

    def __init__(self):
        self.valves = self.Valves()

    async def pipe(self, body: dict, __user__: dict = None, __event_emitter__=None):
        async def emit(event):
            if __event_emitter__:
                await __event_emitter__(event)

        question = body["messages"][-1]["content"]
        await emit({"type": "status", "data": {"description": "Resolving system in FalkorDB…", "done": False}})

        g = FalkorDB(host=self.valves.FALKORDB_HOST, port=self.valves.FALKORDB_PORT).select_graph(self.valves.GRAPH)
        names = [r[0] for r in g.ro_query("MATCH (s:System) RETURN s.name").result_set]
        name = next((n for n in names if n in question), None)
        if not name:
            await emit({"type": "status", "data": {"description": "Unknown system", "done": True}})
            return f"unknown_entity: no system named in the question. Known systems: {', '.join(names)}"

        rows = g.ro_query(DECISIONS_FOR_SYSTEM, {"name": name}).result_set
        await emit({"type": "status", "data": {"description": f"Traversed System←Decision→Doc: {len(rows)} row(s)", "done": True}})
        if not rows:
            return f"not_in_graph: no decision is linked to {name}."

        decision, at, by, doc, url, team = rows[0]
        await emit({"type": "source", "data": {
            "source": {"name": doc, "id": "d-adr-7"},
            "document": [f"{decision} (decided {at} by {by})"],
            "metadata": [{"source": url, "name": doc, "url": url}],
        }})

        hops = [name, decision, doc, by]
        chips = " → ".join(f"<span style='padding:4px 8px;border:1px solid #888;border-radius:6px'>{html.escape(h)}</span>" for h in hops)
        await emit({"type": "embeds", "data": {"embeds": [
            f"<div style='font-family:sans-serif;padding:12px'><b>Graph path</b><div style='margin-top:8px'>{chips}</div></div>"
        ]}})

        return f"**{decision}** ({at}), made by {by}. Owner team: {team}. Source: [{doc}]({url})"
