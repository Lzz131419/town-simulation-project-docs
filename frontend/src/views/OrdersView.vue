<script setup lang="ts">
import { useTown } from "../stores/town";
import { itemNames } from "../types";
import { api } from "../api";
import { Package, Plus } from "lucide-vue-next";

const { catalog, user, world, pending, me, orderForm, perform, who } =
  useTown();
</script>
<template>
  <template v-if="world && me && user"
    ><div class="two-col uneven">
      <div>
        <article class="card">
          <div class="section-heading">
            <h2>街坊的采购需求</h2>
            <span class="tag"
              >{{
                world.orders.filter((o) => o.status === "open").length
              }}
              笔待交付</span
            >
          </div>
          <p v-if="!world.orders.length" class="empty">暂无采购订单</p>
          <article
            v-for="o in [...world.orders].reverse()"
            :key="o.id"
            class="order-row"
          >
            <div class="order-icon"><Package :size="22" /></div>
            <div>
              <strong
                >{{ who(o.buyer_id) }}需要 {{ o.quantity }} 份{{
                  itemNames[o.item]
                }}</strong
              >
              <p>
                每份 {{ o.unit_price }} 镇币 ·
                {{
                  (
                    {
                      open: "资金已托管",
                      filled: "已交付",
                      cancelled: "已取消",
                      expired: "已到期",
                    } as any
                  )[o.status]
                }}
              </p>
            </div>
            <strong class="order-total"
              >{{ o.quantity * o.unit_price }}<small>镇币</small></strong
            ><button
              v-if="o.status === 'open' && o.buyer_id !== user.id"
              class="primary compact"
              :disabled="pending"
              @click="
                perform(
                  () => api(`/orders/${o.id}/fill`, 'POST'),
                  '订单已交付，报酬已到账',
                )
              "
            >
              交付</button
            ><button
              v-if="o.status === 'open' && o.buyer_id === user.id"
              class="quiet compact"
              @click="
                perform(
                  () => api(`/orders/${o.id}/cancel`, 'POST'),
                  '订单已取消，资金已退回',
                )
              "
            >
              取消
            </button>
          </article>
        </article>
      </div>
      <form
        class="card sticky-card"
        @submit.prevent="
          perform(() => api('/orders', 'POST', orderForm), '采购订单已发布')
        "
      >
        <h2>发布一笔采购</h2>
        <label
          >需要什么<select v-model="orderForm.item">
            <option v-for="(item, id) in catalog.items" :key="id" :value="id">
              {{ item.name }}
            </option>
          </select></label
        ><label
          >数量<input
            v-model.number="orderForm.quantity"
            type="number"
            min="1"
            max="10"
            required /></label
        ><label
          >每份报酬<input
            v-model.number="orderForm.unit_price"
            type="number"
            min="1"
            max="50"
            required
        /></label>
        <div class="form-total">
          托管资金<strong
            >{{ orderForm.quantity * orderForm.unit_price }} 镇币</strong
          >
        </div>
        <p class="muted">未交付订单一个小镇日后退款。</p>
        <button class="primary wide" :disabled="pending">
          <Plus :size="16" />发布采购订单
        </button>
      </form>
    </div></template
  >
</template>
