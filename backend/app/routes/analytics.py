import csv
import io

from bson import ObjectId
from bson.errors import InvalidId
from flask import Blueprint, Response, g, jsonify

from app.extensions import mongo
from app.services import analytics as svc
from app.utils.security import login_required
from app.utils.serializers import as_aware, link_json

bp = Blueprint("analytics", __name__, url_prefix="/api/analytics")


def _own_link(link_id):
    try:
        return mongo.links.find_one({"_id": ObjectId(link_id), "owner_id": g.user["_id"]})
    except (InvalidId, TypeError):
        return None


@bp.get("/overview")
@login_required
def overview():
    return jsonify(svc.overview(g.user["_id"]))


@bp.get("/links/<link_id>")
@login_required
def link_analytics(link_id):
    link = _own_link(link_id)
    if not link:
        return jsonify(error="Link not found"), 404
    stats = svc.link_stats(link)
    fc = svc.link_forecast(link)
    anomalies = svc.link_anomalies(link)
    return jsonify(
        link=link_json(link),
        stats=stats,
        forecast=fc,
        anomalies=anomalies,
        insights=svc.insights(link, stats, fc, anomalies),
    )


@bp.get("/links/<link_id>/export")
@login_required
def export_clicks(link_id):
    link = _own_link(link_id)
    if not link:
        return jsonify(error="Link not found"), 404
    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow(["timestamp", "country", "device", "browser", "os", "referrer", "is_bot", "unique"])
    for c in mongo.clicks.find({"link_id": link["_id"]}).sort("ts", -1):
        writer.writerow([
            as_aware(c["ts"]).isoformat(), c.get("country"), c.get("device"), c.get("browser"),
            c.get("os"), c.get("referrer_domain"), c.get("is_bot"), c.get("unique"),
        ])
    return Response(
        buf.getvalue(),
        mimetype="text/csv",
        headers={"Content-Disposition": f"attachment; filename=clicks-{link['short_code']}.csv"},
    )
