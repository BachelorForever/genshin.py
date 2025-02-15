"""Hoyolab component."""
import typing

from genshin import types, utility
from genshin.client import cache as client_cache
from genshin.client import routes
from genshin.client.components import base
from genshin.client.manager import managers
from genshin.models import hoyolab as models

__all__ = ["HoyolabClient"]


class HoyolabClient(base.BaseClient):
    """Hoyolab component."""

    async def search_users(
        self,
        keyword: str,
        *,
        lang: typing.Optional[str] = None,
    ) -> typing.Sequence[models.PartialHoyolabUser]:
        """Search hoyolab users."""
        data = await self.request_hoyolab(
            "community/search/wapi/search/user",
            lang=lang,
            params=dict(keyword=keyword, page_size=20),
            cache=client_cache.cache_key("search", keyword=keyword, lang=self.lang),
        )
        return [models.PartialHoyolabUser(**i["user"]) for i in data["list"]]

    async def get_hoyolab_user(
        self,
        hoyolab_id: typing.Optional[int] = None,
        *,
        lang: typing.Optional[str] = None,
    ) -> models.FullHoyolabUser:
        """Get a hoyolab user."""
        if self.region == types.Region.OVERSEAS:
            url = "/community/painter/wapi/user/full"
        elif self.region == types.Region.CHINESE:
            url = "/user/wapi/getUserFullInfo"
        else:
            raise TypeError(f"{self.region!r} is not a valid region.")

        data = await self.request_bbs(
            url=url,
            lang=lang,
            params=dict(uid=hoyolab_id) if hoyolab_id else None,
            cache=client_cache.cache_key("hoyolab", uid=hoyolab_id, lang=lang or self.lang),
        )
        return models.FullHoyolabUser(**data["user_info"])

    async def get_recommended_users(self, *, limit: int = 200) -> typing.Sequence[models.PartialHoyolabUser]:
        """Get a list of recommended active users."""
        data = await self.request_hoyolab(
            "community/user/wapi/recommendActive",
            params=dict(page_size=limit),
            cache=client_cache.cache_key("recommended"),
        )
        return [models.PartialHoyolabUser(**i["user"]) for i in data["list"]]

    @managers.requires_cookie_token
    async def redeem_code(
        self,
        code: str,
        uid: typing.Optional[int] = None,
        *,
        lang: typing.Optional[str] = None,
    ) -> None:
        """Redeems a gift code for the current genshin user."""
        uid = uid or await self._get_uid(types.Game.GENSHIN)

        await self.request(
            routes.CODE_URL.get_url(),
            params=dict(
                uid=uid,
                region=utility.recognize_genshin_server(uid),
                cdkey=code,
                game_biz="hk4e_global",
                lang=utility.create_short_lang_code(lang or self.lang),
            ),
        )

    @managers.no_multi
    async def check_in_community(self) -> None:
        """Check in to the hoyolab community and claim your daily 5 community exp."""
        url = routes.COMMUNITY_URL.get_url(self.region) / "apihub/wapi/mission/signIn"
        await self.request(url, method="POST", data={})
