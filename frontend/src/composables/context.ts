import type { Ref, ComputedRef } from "vue";
import type { User, Town, Resident, Action } from "../types";
export interface FeatureContext {
  user: Ref<User | null>;
  world: Ref<Town | null>;
  me: ComputedRef<Resident | null>;
  myPlan: ComputedRef<Action[]>;
  perform: (fn: () => Promise<any>, success?: string) => Promise<void>;
  refresh: () => Promise<void>;
  notify: (text: string, isError?: boolean) => void;
}
