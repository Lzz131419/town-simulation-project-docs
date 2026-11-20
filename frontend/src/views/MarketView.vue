<script setup lang="ts">
import { useTown } from "../stores/town";
import { itemNames } from "../types";

import { Trees, ArrowRight, Package, Leaf } from "lucide-vue-next";

const productIcons: Record<string, string> = {
  vegetable: "菜",
  honey: "蜜",
  flax: "麻",
  cloth: "布",
  furniture: "椅",
  soup: "汤",
  grain: "✾",
  bread: "◒",
  wood: "▤",
  fruit: "●",
  fish: "⋈",
  ore: "⬡",
  herb: "❧",
  meal: "◉",
  tool: "⚒",
};
const { user, world, catalog, pending, me, bag, tradeQty, action } = useTown();
</script>
<template>
  <template v-if="world && me && user">
    <div class="toolbar">
      <span
        >我的余额 <strong>{{ me.cash }}</strong> 镇币 · 背包 {{ bag }} 份</span
      ><label class="inline-label"
        >每次交易数量<input
          v-model.number="tradeQty"
          type="number"
          min="1"
          max="10"
      /></label>
    </div>
    <div class="three-col">
      <article
        v-for="(stock, id) in world.market"
        :key="id"
        class="card product-card"
      >
        <span class="product-art" :class="id">{{ productIcons[id] }}</span>
        <h2>{{ itemNames[id] }}</h2>
        <p class="muted">
          集市库存 {{ stock }} · 我持有 {{ me.inventory[id] }}
        </p>
        <div class="price-row">
          <span
            >买入
            <strong>{{ catalog.items[id]?.buy }}</strong>
            镇币</span
          ><span
            >卖出
            <strong>{{ catalog.items[id]?.sell }}</strong>
            镇币</span
          >
        </div>
        <div class="button-row">
          <button
            class="primary"
            :disabled="pending"
            @click="action({ type: 'buy', item: id, quantity: tradeQty })"
          >
            购买</button
          ><button
            :disabled="pending"
            @click="action({ type: 'sell', item: id, quantity: tradeQty })"
          >
            出售
          </button>
          <button
            v-if="['bread', 'fruit', 'meal', 'soup'].includes(id)"
            :disabled="pending || !me.inventory[id]"
            @click="
              action({
                type:
                  id === 'soup'
                    ? 'eat_soup'
                    : id === 'fruit'
                      ? 'eat_fruit'
                      : id === 'meal'
                        ? 'eat_meal'
                        : 'eat',
              })
            "
          >
            食用
          </button>
        </div>
      </article>
    </div>
    <div class="section-heading"><h2>自己动手，也是一种经营</h2></div>
    <div class="three-col">
      <article class="card">
        <Leaf class="green-text" />
        <h3>晨光农场</h3>
        <p>收获3份谷物，消耗9精力。</p>
        <button class="quiet" @click="action({ type: 'farm' })">
          去收获<ArrowRight :size="15" />
        </button>
      </article>
      <article class="card">
        <Package class="ochre-text" />
        <h3>麦香面包房</h3>
        <p>2份谷物烘焙3份面包，消耗6精力。</p>
        <button class="quiet" @click="action({ type: 'bake' })">
          去烘焙<ArrowRight :size="15" />
        </button>
      </article>
      <article class="card">
        <Trees class="green-text" />
        <h3>木作工坊</h3>
        <p>制作2份木材，消耗10精力。</p>
        <button class="quiet" @click="action({ type: 'craft' })">
          去制作<ArrowRight :size="15" />
        </button>
      </article></div
  ></template>
</template>
